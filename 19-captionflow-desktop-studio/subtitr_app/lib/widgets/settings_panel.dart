import 'dart:io';

import 'package:flutter/material.dart';

import '../services/settings_store.dart';

class ModeChoice {
  const ModeChoice({
    required this.value,
    required this.icon,
    required this.title,
    required this.description,
  });

  final String value;
  final IconData icon;
  final String title;
  final String description;
}

class SettingsPanel extends StatelessWidget {
  const SettingsPanel({
    super.key,
    required this.modes,
    required this.mode,
    required this.sourceLang,
    required this.targetLang,
    required this.appearance,
    required this.isRunning,
    required this.onModeChanged,
    required this.onSourceLangChanged,
    required this.onTargetLangChanged,
    required this.onAppearanceChanged,
    this.voice = 'uz-UZ-SardorNeural',
    this.ducking = 0.18,
    this.onVoiceChanged = _ignoreString,
    this.onDuckingChanged = _ignoreDouble,
    this.presets = const [],
    this.onSavePreset = _ignoreVoid,
    this.onApplyPreset = _ignorePreset,
    this.onDeletePreset = _ignorePreset,
    this.onPickSubtitle,
    this.externalSubtitlePath,
    this.onClearSubtitle,
  });

  final List<ModeChoice> modes;
  final String mode;
  final String sourceLang;
  final String targetLang;
  final AppearanceSettings appearance;
  final String voice;
  final double ducking;
  final bool isRunning;
  final ValueChanged<String> onModeChanged;
  final ValueChanged<String> onSourceLangChanged;
  final ValueChanged<String> onTargetLangChanged;
  final ValueChanged<AppearanceSettings> onAppearanceChanged;
  final ValueChanged<String> onVoiceChanged;
  final ValueChanged<double> onDuckingChanged;
  final List<JobPreset> presets;
  final VoidCallback onSavePreset;
  final ValueChanged<JobPreset> onApplyPreset;
  final ValueChanged<JobPreset> onDeletePreset;
  final VoidCallback? onPickSubtitle;
  final String? externalSubtitlePath;
  final VoidCallback? onClearSubtitle;

  static void _ignoreVoid() {}
  static void _ignorePreset(JobPreset _) {}
  static void _ignoreString(String _) {}
  static void _ignoreDouble(double _) {}

  static const _hardsubModes = {
    'dual_vocab',
    'original_vocab',
    'dual',
    'original',
    'translated',
  };

  static const _softsubModes = {
    'softsub',
    'softsub_dual',
    'softsub_translated',
    'softsub_original',
  };

  static const _videoModes = {
    'dual_vocab',
    'original_vocab',
    'dual',
    'original',
    'translated',
    'softsub',
    'softsub_dual',
    'softsub_translated',
    'softsub_original',
    'dubbing',
  };

  List<DropdownMenuItem<String>> _softsubModeItems(ThemeData theme) {
    const items = [
      ('softsub', '2 ta alohida trek (Original + Tarjima CC)', Icons.closed_caption_rounded),
      ('softsub_dual', 'Ikki qatorli subtitr (Asl matn + Tarjima birgalikda)', Icons.subtitles_rounded),
      ('softsub_translated', 'Faqat tarjima (Yagona trek CC)', Icons.translate_rounded),
      ('softsub_original', 'Faqat asl matn (Yagona trek CC)', Icons.text_snippet_rounded),
    ];

    return items.map((item) {
      return DropdownMenuItem<String>(
        value: item.$1,
        child: Row(
          children: [
            Icon(item.$3, size: 20, color: const Color(0xFF0284C7)),
            const SizedBox(width: 12),
            Expanded(child: Text(item.$2, overflow: TextOverflow.ellipsis)),
          ],
        ),
      );
    }).toList();
  }

  List<DropdownMenuItem<String>> _modeItems(ThemeData theme) {
    final video = modes.where((m) => _hardsubModes.contains(m.value));
    final docs = modes.where((m) => !_videoModes.contains(m.value));

    DropdownMenuItem<String> header(String text) => DropdownMenuItem(
      value: '__header_$text',
      enabled: false,
      child: Text(
        text.toUpperCase(),
        style: theme.textTheme.labelSmall?.copyWith(
          color: theme.colorScheme.onSurfaceVariant,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.8,
        ),
      ),
    );

    DropdownMenuItem<String> entry(ModeChoice m) => DropdownMenuItem(
      value: m.value,
      child: Row(
        children: [
          Icon(m.icon, size: 20, color: theme.colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(child: Text(m.title, overflow: TextOverflow.ellipsis)),
        ],
      ),
    );

    return [
      if (video.isNotEmpty) header('Kuydirish uslubi'),
      for (final m in video) entry(m),
      if (docs.isNotEmpty) header('Hujjatlar'),
      for (final m in docs) entry(m),
    ];
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isHardsub = _hardsubModes.contains(mode) ||
        (!_videoModes.contains(mode) && !_softsubModes.contains(mode) && mode != 'dubbing');
    final isSoftsub = _softsubModes.contains(mode);
    final isDubbing = mode == 'dubbing';

    return LayoutBuilder(
      builder: (context, constraints) {
        final hasBoundedHeight = constraints.hasBoundedHeight;
        final showPreview = hasBoundedHeight && constraints.maxHeight >= 600;

        Widget content = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // 1. Eng tepada 3 ta asosiy rejim tugmasi
            _TopModeSelector(
              currentMode: mode,
              enabled: !isRunning,
              onSelectPrimaryMode: onModeChanged,
            ),
            const SizedBox(height: 10),
            _PresetRow(
              presets: presets,
              enabled: !isRunning,
              onSave: onSavePreset,
              onApply: onApplyPreset,
              onDelete: onDeletePreset,
              onPickSubtitle: onPickSubtitle,
              externalSubtitlePath: externalSubtitlePath,
              onClearSubtitle: onClearSubtitle,
            ),
            const SizedBox(height: 10),

            // 2. Rejimga mos sozlamalar bloki
            if (isHardsub) ...[
              DropdownButtonFormField<String>(
                initialValue: _hardsubModes.contains(mode) || !_videoModes.contains(mode) ? mode : 'dual_vocab',
                decoration: InputDecoration(
                  labelText: 'Kuydirish uslubi',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.surface,
                ),
                isExpanded: true,
                items: _modeItems(theme),
                onChanged: isRunning
                    ? null
                    : (v) {
                        if (v != null) onModeChanged(v);
                      },
              ),
              const SizedBox(height: 10),
            ] else if (isSoftsub) ...[
              DropdownButtonFormField<String>(
                initialValue: _softsubModes.contains(mode) ? mode : 'softsub',
                decoration: InputDecoration(
                  labelText: 'Yumshoq subtitr uslubi',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.surface,
                ),
                isExpanded: true,
                items: _softsubModeItems(theme),
                onChanged: isRunning
                    ? null
                    : (v) {
                        if (v != null) onModeChanged(v);
                      },
              ),
              const SizedBox(height: 10),
            ],

            // 3. Til tanlash
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: sourceLang,
                    isExpanded: true,
                    decoration: InputDecoration(
                      labelText: 'Video tili',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      filled: true,
                      fillColor: theme.colorScheme.surface,
                    ),
                    items: const [
                      DropdownMenuItem(value: 'auto', child: Text('Avtomatik')),
                      DropdownMenuItem(value: 'en', child: Text('Ingliz')),
                      DropdownMenuItem(value: 'ru', child: Text('Rus')),
                      DropdownMenuItem(value: 'uz', child: Text("O'zbek")),
                      DropdownMenuItem(value: 'tr', child: Text('Turk')),
                      DropdownMenuItem(value: 'kk', child: Text('Qozoq')),
                      DropdownMenuItem(value: 'tg', child: Text('Tojik')),
                      DropdownMenuItem(value: 'ky', child: Text("Qirg'iz")),
                    ],
                    onChanged: isRunning
                        ? null
                        : (v) {
                            if (v != null) onSourceLangChanged(v);
                          },
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: targetLang,
                    isExpanded: true,
                    decoration: InputDecoration(
                      labelText: 'Tarjima tili',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      filled: true,
                      fillColor: theme.colorScheme.surface,
                    ),
                    items: const [
                      DropdownMenuItem(value: 'uz', child: Text("O'zbek")),
                      DropdownMenuItem(value: 'en', child: Text('Ingliz')),
                      DropdownMenuItem(value: 'ru', child: Text('Rus')),
                      DropdownMenuItem(value: 'tr', child: Text('Turk')),
                      DropdownMenuItem(value: 'kk', child: Text('Qozoq')),
                      DropdownMenuItem(value: 'tg', child: Text('Tojik')),
                      DropdownMenuItem(value: 'ky', child: Text("Qirg'iz")),
                    ],
                    onChanged: isRunning
                        ? null
                        : (v) {
                            if (v != null) onTargetLangChanged(v);
                          },
                  ),
                ),
              ],
            ),

            // 4. AI Dublyaj parametrlari
            if (isDubbing) ...[
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: _VoiceChoiceCard(
                      title: 'Sardor',
                      subtitle: 'Erkak ovozi',
                      icon: Icons.face_rounded,
                      isSelected: voice.contains('Sardor'),
                      enabled: !isRunning,
                      onTap: () => onVoiceChanged('uz-UZ-SardorNeural'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _VoiceChoiceCard(
                      title: 'Madina',
                      subtitle: 'Ayol ovozi',
                      icon: Icons.face_3_rounded,
                      isSelected: voice.contains('Madina'),
                      enabled: !isRunning,
                      onTap: () => onVoiceChanged('uz-UZ-MadinaNeural'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<double>(
                initialValue: ducking,
                isExpanded: true,
                decoration: InputDecoration(
                  labelText: 'Asl fon ovozi balandligi (Ducking)',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 12,
                  ),
                  filled: true,
                  fillColor: theme.colorScheme.surface,
                ),
                items: const [
                  DropdownMenuItem(
                    value: 0.18,
                    child: Text('18% — Tavsiya (Musiqa va effektlar eshitiladi)'),
                  ),
                  DropdownMenuItem(
                    value: 0.10,
                    child: Text('10% — Past fon (AI ovoz yanada aniq)'),
                  ),
                  DropdownMenuItem(
                    value: 0.00,
                    child: Text("0% — Faqat AI nutq (Asl audio o'chiriladi)"),
                  ),
                  DropdownMenuItem(
                    value: 0.30,
                    child: Text('30% — Baland fon (Musiqiy orqa fon)'),
                  ),
                ],
                onChanged: isRunning
                    ? null
                    : (v) {
                        if (v != null) onDuckingChanged(v);
                      },
              ),
            ],

            // 5. Subtitr tashqi ko'rinish sozlamalari (Kuydirish va Yumshoq rejimlar)
            if (_hardsubModes.contains(mode) || isSoftsub) ...[
              const SizedBox(height: 10),
              _AppearanceRow(
                appearance: appearance,
                enabled: !isRunning,
                onChanged: onAppearanceChanged,
                showOrigStyle: mode != 'translated' && mode != 'softsub_translated',
              ),
            ],

            // 6. Namunali ko'rinish
            if (showPreview)
              Expanded(
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: _ModePreview(
                    key: ValueKey(
                      '$mode|${appearance.subColor}|${appearance.origStyle}|$voice|$ducking',
                    ),
                    mode: mode,
                    subColor: appearance.subColor,
                    origStyle: appearance.origStyle,
                    voice: voice,
                    ducking: ducking,
                  ),
                ),
              ),
          ],
        );

        if (!showPreview) {
          if (!hasBoundedHeight) {
            return content;
          }
          return SingleChildScrollView(
            child: content,
          );
        }
        return content;
      },
    );
  }
}

/// Eng tepada joylashgan 3 ta asosiy rejim tugmasi
class _TopModeSelector extends StatelessWidget {
  const _TopModeSelector({
    required this.currentMode,
    required this.enabled,
    required this.onSelectPrimaryMode,
  });

  final String currentMode;
  final bool enabled;
  final ValueChanged<String> onSelectPrimaryMode;

  @override
  Widget build(BuildContext context) {
    final isHardsub = SettingsPanel._hardsubModes.contains(currentMode) ||
        (!SettingsPanel._videoModes.contains(currentMode) &&
            !SettingsPanel._softsubModes.contains(currentMode) &&
            currentMode != 'dubbing');
    final isSoftsub = SettingsPanel._softsubModes.contains(currentMode);
    final isDubbing = currentMode == 'dubbing';

    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: const Color(0xFF141416),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF26262B)),
      ),
      child: Row(
        children: [
          Expanded(
            child: _ModeTabButton(
              icon: Icons.movie_filter_rounded,
              title: 'Kuydirish',
              subtitle: 'Hardsub',
              isSelected: isHardsub,
              activeColor: const Color(0xFF2563EB),
              textColor: Colors.white,
              enabled: enabled,
              onTap: () => onSelectPrimaryMode(
                SettingsPanel._hardsubModes.contains(currentMode) ? currentMode : 'dual_vocab',
              ),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _ModeTabButton(
              icon: Icons.closed_caption_rounded,
              title: 'Yumshoq',
              subtitle: 'Softsub (CC)',
              isSelected: isSoftsub,
              activeColor: const Color(0xFF0284C7),
              textColor: Colors.white,
              enabled: enabled,
              onTap: () => onSelectPrimaryMode(
                SettingsPanel._softsubModes.contains(currentMode) ? currentMode : 'softsub',
              ),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _ModeTabButton(
              icon: Icons.record_voice_over_rounded,
              title: 'AI Dublyaj',
              subtitle: "O'zgartirish",
              isSelected: isDubbing,
              activeColor: const Color(0xFF7C3AED),
              textColor: Colors.white,
              enabled: enabled,
              onTap: () => onSelectPrimaryMode('dubbing'),
            ),
          ),
        ],
      ),
    );
  }
}

class _ModeTabButton extends StatelessWidget {
  const _ModeTabButton({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.isSelected,
    required this.activeColor,
    required this.textColor,
    required this.enabled,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool isSelected;
  final Color activeColor;
  final Color textColor;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: enabled ? onTap : null,
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
          decoration: BoxDecoration(
            color: isSelected ? activeColor : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: activeColor.withValues(alpha: 0.28),
                      blurRadius: 6,
                      offset: const Offset(0, 1.5),
                    ),
                  ]
                : null,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 16,
                color: isSelected ? textColor : const Color(0xFF94A3B8),
              ),
              const SizedBox(width: 6),
              Flexible(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                        color: isSelected ? textColor : const Color(0xFFD4D4D8),
                        height: 1.15,
                      ),
                    ),
                    Text(
                      subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w400,
                        color: isSelected
                            ? textColor.withValues(alpha: 0.8)
                            : const Color(0xFF71717A),
                        height: 1.15,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _VoiceChoiceCard extends StatelessWidget {
  const _VoiceChoiceCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.isSelected,
    required this.enabled,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final bool isSelected;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    const activeColor = Color(0xFFA855F7);
    return InkWell(
      onTap: enabled ? onTap : null,
      borderRadius: BorderRadius.circular(10),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
        decoration: BoxDecoration(
          color: isSelected
              ? activeColor.withValues(alpha: 0.16)
              : const Color(0xFF1B1B1B),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isSelected ? activeColor : const Color(0xFF333333),
            width: isSelected ? 1.5 : 1.0,
          ),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              size: 22,
              color: isSelected ? activeColor : const Color(0xFF9E9E9E),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 12.5,
                      color: isSelected ? Colors.white : const Color(0xFFCCCCCC),
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 10.5,
                      color: isSelected
                          ? const Color(0xFFD8B4FE)
                          : const Color(0xFF888888),
                    ),
                  ),
                ],
              ),
            ),
            if (isSelected)
              const Icon(Icons.check_circle_rounded, size: 16, color: activeColor),
          ],
        ),
      ),
    );
  }
}

class _PresetRow extends StatelessWidget {
  const _PresetRow({
    required this.presets,
    required this.enabled,
    required this.onSave,
    required this.onApply,
    required this.onDelete,
    this.onPickSubtitle,
    this.externalSubtitlePath,
    this.onClearSubtitle,
  });

  final List<JobPreset> presets;
  final bool enabled;
  final VoidCallback onSave;
  final ValueChanged<JobPreset> onApply;
  final ValueChanged<JobPreset> onDelete;
  final VoidCallback? onPickSubtitle;
  final String? externalSubtitlePath;
  final VoidCallback? onClearSubtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      children: [
        if (onPickSubtitle != null) ...[
          Tooltip(
            message: externalSubtitlePath == null
                ? 'Tashqi SRT/ASS subtitr import qilish'
                : 'Subtitr: ${File(externalSubtitlePath!).uri.pathSegments.last} (o\'zgartirish)',
            child: OutlinedButton.icon(
              onPressed: enabled ? onPickSubtitle : null,
              icon: Icon(
                externalSubtitlePath == null
                    ? Icons.subtitles_outlined
                    : Icons.check_circle_rounded,
                size: 16,
                color: externalSubtitlePath == null
                    ? const Color(0xFF94A3B8)
                    : const Color(0xFF10B981),
              ),
              label: Text(
                externalSubtitlePath == null ? 'SRT / ASS' : 'SRT',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: externalSubtitlePath == null
                      ? const Color(0xFFE2E8F0)
                      : const Color(0xFF10B981),
                ),
              ),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
                side: BorderSide(
                  color: externalSubtitlePath == null
                      ? const Color(0xFF333338)
                      : const Color(0xFF10B981).withValues(alpha: 0.6),
                ),
                backgroundColor: externalSubtitlePath == null
                    ? const Color(0xFF16181D)
                    : const Color(0xFF10B981).withValues(alpha: 0.1),
              ),
            ),
          ),
          if (externalSubtitlePath != null && onClearSubtitle != null) ...[
            const SizedBox(width: 4),
            IconButton(
              icon: const Icon(Icons.close_rounded, size: 16),
              tooltip: 'Subtitrni tozalash',
              visualDensity: VisualDensity.compact,
              onPressed: enabled ? onClearSubtitle : null,
            ),
          ],
          const SizedBox(width: 8),
        ],
        Expanded(
          child: DropdownButtonFormField<String>(
            initialValue: null,
            isExpanded: true,
            decoration: InputDecoration(
              labelText: 'Saqlangan sozlamalar',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 14,
                vertical: 10,
              ),
              filled: true,
              fillColor: theme.colorScheme.surface,
            ),
            items: [
              if (presets.isEmpty)
                const DropdownMenuItem(
                  value: '__empty',
                  enabled: false,
                  child: Text(
                    'Hali saqlanmagan',
                    style: TextStyle(color: Colors.grey),
                  ),
                )
              else
                for (final p in presets)
                  DropdownMenuItem(
                    value: p.name,
                    child: Text(
                      p.name,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
            ],
            onChanged: (name) {
              if (name == null || name == '__empty') return;
              final match = presets.firstWhere((p) => p.name == name);
              onApply(match);
            },
          ),
        ),
        const SizedBox(width: 8),
        IconButton.filledTonal(
          icon: const Icon(Icons.bookmark_add_outlined),
          tooltip: 'Joriy sozlamalarni saqlash',
          onPressed: enabled ? onSave : null,
        ),
        if (presets.isNotEmpty) ...[
          const SizedBox(width: 6),
          IconButton.outlined(
            icon: const Icon(Icons.delete_outline, size: 20),
            tooltip: "Presetni o'chirish",
            onPressed: enabled
                ? () async {
                    final target = await showDialog<JobPreset>(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        icon: const Icon(Icons.delete_outline_rounded),
                        title: const Text("Presetni o'chirish"),
                        content: SizedBox(
                          width: 320,
                          child: ListView.separated(
                            shrinkWrap: true,
                            itemCount: presets.length,
                            separatorBuilder: (_, _) => const Divider(height: 1),
                            itemBuilder: (_, i) {
                              final item = presets[i];
                              return ListTile(
                                title: Text(item.name),
                                subtitle: Text('${item.mode} · ${item.target}'),
                                trailing: const Icon(Icons.delete_forever_rounded, color: Colors.redAccent),
                                onTap: () => Navigator.pop(ctx, item),
                              );
                            },
                          ),
                        ),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(ctx),
                            child: const Text('Yopish'),
                          ),
                        ],
                      ),
                    );
                    if (target != null) {
                      onDelete(target);
                    }
                  }
                : null,
          ),
        ],
      ],
    );
  }
}

class _AppearanceRow extends StatelessWidget {
  const _AppearanceRow({
    required this.appearance,
    required this.enabled,
    required this.onChanged,
    this.showOrigStyle = true,
  });

  final AppearanceSettings appearance;
  final bool enabled;
  final ValueChanged<AppearanceSettings> onChanged;
  final bool showOrigStyle;

  static const _colors = {
    '#94A3B8': 'Kulrang',
    '#39FF14': 'Neon yashil',
    '#FFE680': 'Sariq',
    '#FFFFFF': 'Oq',
    '#00E5FF': "Ko'k",
    '#FF2D95': 'Pushti',
  };

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(children: _rowOne()),
        const SizedBox(height: 8),
        Row(children: _rowTwo()),
      ],
    );
  }

  List<Widget> _rowOne() {
    return [
      Expanded(
        child: _MiniDropdown<double>(
          label: 'Shrift',
          value: appearance.fontScale,
          items: {0.85: 'Kichik', 1.0: "O'rta", 1.2: 'Katta'},
          enabled: enabled,
          onChanged: (v) => onChanged(appearance.copyWith(fontScale: v)),
        ),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: _MiniDropdown<String>(
          label: 'Joyi',
          value: appearance.position,
          items: const {'bottom': 'Past', 'top': 'Tepa'},
          enabled: enabled,
          onChanged: (v) => onChanged(appearance.copyWith(position: v)),
        ),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: _MiniDropdown<String>(
          label: 'Sifat',
          value: appearance.quality,
          items: const {
            '720': '720p',
            '1080': '1080p',
            '1440': '2K',
            '2160': '4K',
          },
          enabled: enabled,
          onChanged: (v) => onChanged(appearance.copyWith(quality: v)),
        ),
      ),
    ];
  }

  List<Widget> _rowTwo() {
    return [
      Expanded(
        child: _MiniDropdown<bool>(
          label: 'Kattalash',
          value: appearance.upscale,
          items: const {false: "Yo'q", true: 'Ha'},
          enabled: enabled,
          onChanged: (v) => onChanged(appearance.copyWith(upscale: v)),
        ),
      ),
      const SizedBox(width: 8),
      if (showOrigStyle) ...[
        Expanded(
          child: _MiniDropdown<String>(
            label: 'Asl matn',
            value: appearance.origStyle,
            items: const {'box': 'Sariq quti', 'plain': 'Oddiy'},
            enabled: enabled,
            onChanged: (v) => onChanged(appearance.copyWith(origStyle: v)),
          ),
        ),
        const SizedBox(width: 8),
      ],
      Expanded(
        child: _MiniDropdown<String>(
          label: 'Rang',
          value: _colors.containsKey(appearance.subColor)
              ? appearance.subColor
              : '#39FF14',
          items: _colors,
          enabled: enabled,
          onChanged: (v) => onChanged(appearance.copyWith(subColor: v)),
        ),
      ),
    ];
  }
}

class _MiniDropdown<T> extends StatelessWidget {
  const _MiniDropdown({
    required this.label,
    required this.value,
    required this.items,
    required this.enabled,
    required this.onChanged,
  });

  final String label;
  final T value;
  final Map<T, String> items;
  final bool enabled;
  final ValueChanged<T> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<T>(
      initialValue: value,
      isDense: true,
      isExpanded: true,
      decoration: InputDecoration(
        labelText: label,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 8,
          vertical: 10,
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      ),
      items: [
        for (final e in items.entries)
          DropdownMenuItem(value: e.key, child: Text(e.value)),
      ],
      onChanged: enabled
          ? (v) {
              if (v != null) onChanged(v);
            }
          : null,
    );
  }
}

class _ModePreview extends StatelessWidget {
  final String mode;
  final String subColor;
  final String origStyle;
  final String voice;
  final double ducking;

  const _ModePreview({
    super.key,
    required this.mode,
    this.subColor = '#39FF14',
    this.origStyle = 'box',
    this.voice = 'uz-UZ-SardorNeural',
    this.ducking = 0.18,
  });

  Color get _subColor {
    final hex = subColor.replaceAll('#', '');
    final value = int.tryParse(hex, radix: 16);
    return value == null ? const Color(0xFF39FF14) : Color(0xFF000000 | value);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    Widget content;
    switch (mode) {
      case 'softsub':
      case 'softsub_dual':
      case 'softsub_translated':
      case 'softsub_original':
        final effectiveSubColor = (subColor == '#39FF14' || subColor == '#94A3B8')
            ? const Color(0xFF94A3B8)
            : _subColor;

        final String badgeTitle;
        final bool showOrig;
        final bool showTrans;

        switch (mode) {
          case 'softsub_original':
            badgeTitle = 'CC: Faqat Asl Matn';
            showOrig = true;
            showTrans = false;
            break;
          case 'softsub_translated':
            badgeTitle = 'CC: Faqat Tarjima';
            showOrig = false;
            showTrans = true;
            break;
          case 'softsub_dual':
            badgeTitle = 'CC: Birgalikda (2 qator)';
            showOrig = true;
            showTrans = true;
            break;
          case 'softsub':
          default:
            badgeTitle = 'CC: 2 ta alohida trek';
            showOrig = true;
            showTrans = true;
            break;
        }

        content = Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF222222)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF141416), Color(0xFF0A0A0C)],
            ),
          ),
          child: Stack(
            children: [
              Positioned(
                top: 14,
                right: 14,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0284C7).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFF0284C7).withValues(alpha: 0.4)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.closed_caption_rounded, size: 16, color: Color(0xFF38BDF8)),
                      const SizedBox(width: 5),
                      Text(
                        badgeTitle,
                        style: const TextStyle(
                          color: Color(0xFF38BDF8),
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Positioned(
                bottom: 20,
                left: 16,
                right: 16,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (showOrig)
                      if (origStyle == 'box')
                        Container(
                          color: const Color(0xFF334155),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          child: const Text(
                            'This is the original English subtitle',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: Color(0xFFE2E8F0),
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        )
                      else
                        const Text(
                          'This is the original English subtitle',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Color(0xFFE2E8F0),
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                          ),
                        ),
                    if (showOrig && showTrans) const SizedBox(height: 5),
                    if (showTrans)
                      Text(
                        "Bu o'zbekcha tarjima qilingan subtitr",
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: effectiveSubColor,
                          fontSize: 13.5,
                          fontWeight: FontWeight.w800,
                          shadows: const [Shadow(blurRadius: 4, color: Colors.black)],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        );
        break;

      case 'dubbing':
        final isMadina = voice.contains('Madina');
        final voiceName = isMadina ? 'Madina (Ayol)' : 'Sardor (Erkak)';
        final duckingPct = (ducking * 100).toInt();

        content = Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF222222)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF141416), Color(0xFF0A0A0C)],
            ),
          ),
          child: Stack(
            children: [
              Positioned(
                top: 14,
                right: 14,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF7C3AED).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFF7C3AED).withValues(alpha: 0.4)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.record_voice_over_rounded, size: 15, color: Color(0xFFA78BFA)),
                      SizedBox(width: 5),
                      Text(
                        'Multi-Audio: 2 trek',
                        style: TextStyle(
                          color: Color(0xFFA78BFA),
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        for (final h in [6.0, 12.0, 20.0, 10.0, 28.0, 18.0, 32.0, 22.0, 14.0, 26.0, 16.0, 30.0, 12.0, 7.0])
                          Container(
                            margin: const EdgeInsets.symmetric(horizontal: 2),
                            width: 3.5,
                            height: h,
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [Color(0xFFA78BFA), Color(0xFF7C3AED)],
                              ),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1A1A1E),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFF2E2E38)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.headphones_rounded, size: 12, color: Color(0xFF94A3B8)),
                          const SizedBox(width: 4),
                          Text(
                            'Fon: $duckingPct%',
                            style: const TextStyle(
                              color: Color(0xFF94A3B8),
                              fontSize: 10.5,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 6),
                            child: Text('•', style: TextStyle(color: Color(0xFF475569), fontSize: 10)),
                          ),
                          const Icon(Icons.mic_rounded, size: 12, color: Color(0xFFA78BFA)),
                          const SizedBox(width: 4),
                          Text(
                            voiceName,
                            style: const TextStyle(
                              color: Color(0xFFDDD6FE),
                              fontSize: 10.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Positioned(
                bottom: 20,
                left: 16,
                right: 16,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      'This is the original English speech',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Color(0xFF64748B),
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                      ),
                    ),
                    const SizedBox(height: 5),
                    const Text(
                      "🗣️ \"Bu o'zbekcha AI dublyaj qilingan nutq\"",
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Color(0xFFF1F5F9),
                        fontSize: 13.5,
                        fontWeight: FontWeight.w800,
                        shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
        break;

      case 'dual_vocab':
      case 'original_vocab':
      case 'dual':
      case 'original':
      case 'translated':
        final hasVocab = mode.contains('vocab');
        final showOriginal = mode != 'translated';
        final isDual = mode.startsWith('dual') || mode == 'translated';

        content = Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF222222)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF141416), Color(0xFF0A0A0C)],
            ),
          ),
          child: Stack(
            children: [
              if (hasVocab)
                Positioned(
                  left: 16,
                  bottom: 50,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    verticalDirection: VerticalDirection.up,
                    children: [
                      _vocabLine('apple', 'olma'),
                      _vocabLine('run', 'yugurmoq'),
                      _vocabLine('fast', 'tez'),
                    ],
                  ),
                ),
              Positioned(
                bottom: 16,
                left: 0,
                right: 0,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (showOriginal)
                      if (origStyle == 'box')
                        Container(
                          color: const Color(0xFFFFD400),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 2,
                          ),
                          child: const Text(
                            'This is the original text',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              color: Colors.black,
                              fontSize: 13,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        )
                      else
                        const Text(
                          'This is the original text',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w900,
                            shadows: [
                              Shadow(blurRadius: 4, color: Colors.black),
                            ],
                          ),
                        ),
                    if (isDual)
                      Text(
                        'Bu tarjima qilingan matn',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          color: _subColor,
                          fontSize: showOriginal ? 13 : 15,
                          fontWeight: FontWeight.w900,
                          shadows: const [
                            Shadow(blurRadius: 4, color: Colors.black),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        );
        break;

      case 'reading':
        content = Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(
              alpha: 0.3,
            ),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: theme.colorScheme.outlineVariant),
          ),
          child: Center(
            child: FittedBox(
              fit: BoxFit.contain,
              child: Container(
                width: 140,
                height: 198,
                padding: const EdgeInsets.fromLTRB(14, 13, 14, 10),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(3),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.18),
                      blurRadius: 10,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _PaperLine(
                      widthFactor: 0.72,
                      height: 5,
                      color: Color(0xFF15171A),
                    ),
                    const SizedBox(height: 5),
                    const _PaperLine(
                      widthFactor: 0.36,
                      height: 2.5,
                      color: Color(0xFFB4B9C2),
                    ),
                    const SizedBox(height: 7),
                    Container(height: 0.6, color: const Color(0xFFD7DAE0)),
                    const SizedBox(height: 8),
                    for (final last in const [0.55, 0.84, 0.42, 0.70]) ...[
                      for (var i = 0; i < 3; i++) ...[
                        const _PaperLine(widthFactor: 1.0, height: 2.4),
                        const SizedBox(height: 4),
                      ],
                      _PaperLine(widthFactor: last, height: 2.4),
                      const SizedBox(height: 9),
                    ],
                  ],
                ),
              ),
            ),
          ),
        );
        break;

      case 'srt':
      case 'transcript':
      case 'vocabulary':
      case 'all':
      default:
        content = Container(
          width: double.infinity,
          height: 140,
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(
              alpha: 0.3,
            ),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(
              color: theme.colorScheme.outlineVariant,
              style: BorderStyle.solid,
            ),
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  mode == 'all'
                      ? Icons.all_inclusive_rounded
                      : Icons.description_rounded,
                  size: 36,
                  color: theme.colorScheme.primary.withValues(alpha: 0.7),
                ),
                const SizedBox(height: 12),
                Text(
                  mode == 'all'
                      ? "Barcha fayllar (Video, Matn, Lug'at, SRT)"
                      : 'Faqat hujjat fayllari yaratiladi',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        );
        break;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text(
          'Namuna',
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.primary,
          ),
        ),
        const SizedBox(height: 10),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: content,
          ),
        ),
      ],
    );
  }

  Widget _vocabLine(String en, String uz) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: RichText(
        text: TextSpan(
          children: [
            TextSpan(
              text: en,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.w900,
                shadows: [Shadow(blurRadius: 3, color: Colors.black)],
              ),
            ),
            const TextSpan(
              text: '  ·  ',
              style: TextStyle(
                color: Color(0xFF8A93A6),
                fontSize: 13,
                fontWeight: FontWeight.w900,
              ),
            ),
            TextSpan(
              text: uz,
              style: TextStyle(
                color: _subColor,
                fontSize: 13,
                fontWeight: FontWeight.w900,
                shadows: const [Shadow(blurRadius: 3, color: Colors.black)],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PaperLine extends StatelessWidget {
  const _PaperLine({
    required this.widthFactor,
    required this.height,
    this.color = const Color(0xFFCDD1D8),
  });

  final double widthFactor;
  final double height;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return FractionallySizedBox(
      alignment: Alignment.centerLeft,
      widthFactor: widthFactor,
      child: Container(
        height: height,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(height / 2),
        ),
      ),
    );
  }
}
