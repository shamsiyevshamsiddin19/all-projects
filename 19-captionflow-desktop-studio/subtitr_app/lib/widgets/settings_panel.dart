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

  static const _videoModes = {
    'dual_vocab',
    'original_vocab',
    'dual',
    'original',
    'translated',
    'softsub',
    'dubbing',
  };

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
        (!_videoModes.contains(mode) && mode != 'softsub' && mode != 'dubbing');
    final isSoftsub = mode == 'softsub';
    final isDubbing = mode == 'dubbing';

    return LayoutBuilder(
      builder: (context, constraints) {
        final showPreview = constraints.maxHeight >= 600;

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
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF0B192C),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: const Color(0xFF38BDF8).withValues(alpha: 0.35),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.closed_caption_rounded,
                      color: Color(0xFF38BDF8),
                      size: 22,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "2 ta subtitr (Original + Tarjima) — Kuydirmasdan",
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 12.5,
                              color: Color(0xFFF0F9FF),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "Subtitrlar video kadriga kuydirilmaydi, alohida trek qilib muxlanadi. 1-2 soniyada tayyor bo'ladi va video sifati 100% saqlanadi.",
                            style: TextStyle(
                              fontSize: 11,
                              color: const Color(0xFF93C5FD).withValues(alpha: 0.85),
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),
            ] else if (isDubbing) ...[
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF1F0E38),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: const Color(0xFFA855F7).withValues(alpha: 0.35),
                  ),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.graphic_eq_rounded,
                      color: Color(0xFFA855F7),
                      size: 22,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "AI Dublyaj — Ko'p tilli audio treklar (Multi-audio)",
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              fontSize: 12.5,
                              color: Color(0xFFFAF5FF),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "Videoga 2 ta audio yo'lak yoziladi: 1-Asl ovoz, 2-O'zbekcha AI Dublyaj. Asl musiqa orqa fonda saqlanadi (ducking).",
                            style: TextStyle(
                              fontSize: 11,
                              color: const Color(0xFFD8B4FE).withValues(alpha: 0.85),
                              height: 1.3,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
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

            // 5. Hardsub tashqi ko'rinish sozlamalari
            if (_hardsubModes.contains(mode)) ...[
              const SizedBox(height: 10),
              _AppearanceRow(
                appearance: appearance,
                enabled: !isRunning,
                onChanged: onAppearanceChanged,
                showOrigStyle: mode != 'translated',
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
        (!SettingsPanel._videoModes.contains(currentMode) && currentMode != 'softsub' && currentMode != 'dubbing');
    final isSoftsub = currentMode == 'softsub';
    final isDubbing = currentMode == 'dubbing';

    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF141414),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF262626)),
      ),
      child: Row(
        children: [
          Expanded(
            child: _ModeTabButton(
              icon: Icons.movie_filter_rounded,
              title: 'Kuydirish',
              subtitle: 'Hardsub',
              isSelected: isHardsub,
              activeColor: const Color(0xFFFFD400),
              textColor: Colors.black,
              enabled: enabled,
              onTap: () => onSelectPrimaryMode('dual_vocab'),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _ModeTabButton(
              icon: Icons.closed_caption_rounded,
              title: 'Yumshoq',
              subtitle: '2 subtitr (CC)',
              isSelected: isSoftsub,
              activeColor: const Color(0xFF38BDF8),
              textColor: const Color(0xFF0F172A),
              enabled: enabled,
              onTap: () => onSelectPrimaryMode('softsub'),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _ModeTabButton(
              icon: Icons.record_voice_over_rounded,
              title: 'AI Dublyaj',
              subtitle: "O'zgartirish",
              isSelected: isDubbing,
              activeColor: const Color(0xFFA855F7),
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
        borderRadius: BorderRadius.circular(9),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
          decoration: BoxDecoration(
            color: isSelected ? activeColor : Colors.transparent,
            borderRadius: BorderRadius.circular(9),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: activeColor.withValues(alpha: 0.28),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : null,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 20,
                color: isSelected ? textColor : const Color(0xFF9E9E9E),
              ),
              const SizedBox(height: 3),
              Text(
                title,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: isSelected ? textColor : const Color(0xFFE2E8F0),
                ),
              ),
              const SizedBox(height: 1),
              Text(
                subtitle,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                  color: isSelected
                      ? textColor.withValues(alpha: 0.8)
                      : const Color(0xFF757575),
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
  });

  final List<JobPreset> presets;
  final bool enabled;
  final VoidCallback onSave;
  final ValueChanged<JobPreset> onApply;
  final ValueChanged<JobPreset> onDelete;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      children: [
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
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            p.name,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete_outline, size: 18),
                          tooltip: "O'chirish",
                          onPressed: () => onDelete(p),
                        ),
                      ],
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
        content = Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.3)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF0A1828), Color(0xFF050C16)],
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
                    color: const Color(0xFF38BDF8).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.4)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.closed_caption_rounded, size: 16, color: Color(0xFF38BDF8)),
                      SizedBox(width: 5),
                      Text(
                        'CC: 2 ta alohida trek',
                        style: TextStyle(
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
                top: 14,
                left: 14,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.green.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    '⚡ Tezkor Mux (~1.5 soniya)',
                    style: TextStyle(
                      color: Colors.greenAccent,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
              Positioned(
                bottom: 24,
                left: 16,
                right: 16,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      'This is the original English subtitle',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "Bu o'zbekcha tarjima qilingan subtitr (Softsub)",
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Color(0xFF38BDF8),
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                        shadows: [Shadow(blurRadius: 4, color: Colors.black)],
                      ),
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.5),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        "Pleyerda subtitrni o'chirib/yoqish mumkin",
                        style: TextStyle(color: Color(0xFF94A3B8), fontSize: 10.5),
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
            border: Border.all(color: const Color(0xFFA855F7).withValues(alpha: 0.3)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF1B0C2E), Color(0xFF0C0517)],
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
                    color: const Color(0xFFA855F7).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0xFFA855F7).withValues(alpha: 0.4)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.graphic_eq_rounded, size: 16, color: Color(0xFFA855F7)),
                      SizedBox(width: 5),
                      Text(
                        'Multi-Audio: 2 trek',
                        style: TextStyle(
                          color: Color(0xFFA855F7),
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Positioned(
                top: 14,
                left: 14,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFFA855F7).withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    '🎙️ Microsoft Edge TTS',
                    style: TextStyle(
                      color: Color(0xFFD8B4FE),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
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
                        for (final h in [8.0, 16.0, 26.0, 12.0, 32.0, 22.0, 36.0, 25.0, 14.0, 28.0, 18.0, 34.0, 14.0, 9.0])
                          Container(
                            margin: const EdgeInsets.symmetric(horizontal: 2.5),
                            width: 4,
                            height: h,
                            decoration: BoxDecoration(
                              gradient: const LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [Color(0xFFC084FC), Color(0xFFA855F7)],
                              ),
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.4),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFF333333)),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '1-trek: 🎧 Asl fon ovozi (Ducking: $duckingPct%)',
                            style: const TextStyle(
                              color: Color(0xFFCBD5E1),
                              fontSize: 11.5,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            "2-trek: 🗣️ O'zbekcha AI Dublyaj ($voiceName)",
                            style: const TextStyle(
                              color: Color(0xFFF3E8FF),
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
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
              colors: [Color(0xFF1A1A1A), Color(0xFF0A0A0A)],
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
