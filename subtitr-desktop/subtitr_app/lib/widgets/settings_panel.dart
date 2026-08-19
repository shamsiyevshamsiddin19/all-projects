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
  });

  final List<ModeChoice> modes;
  final String mode;
  final String sourceLang;
  final String targetLang;
  final AppearanceSettings appearance;
  final bool isRunning;
  final ValueChanged<String> onModeChanged;
  final ValueChanged<String> onSourceLangChanged;
  final ValueChanged<String> onTargetLangChanged;
  final ValueChanged<AppearanceSettings> onAppearanceChanged;

  static const _videoModes = {'dual_vocab', 'original_vocab', 'dual', 'original'};

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        DropdownButtonFormField<String>(
          initialValue: mode,
          decoration: InputDecoration(
            labelText: 'Natija turi',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            filled: true,
            fillColor: theme.colorScheme.surface,
          ),
          items: [
            for (final m in modes)
              DropdownMenuItem(
                value: m.value,
                child: Row(
                  children: [
                    Icon(m.icon, size: 20, color: theme.colorScheme.primary),
                    const SizedBox(width: 12),
                    Text(m.title),
                  ],
                ),
              ),
          ],
          onChanged: isRunning ? null : (v) {
            if (v != null) onModeChanged(v);
          },
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                initialValue: sourceLang,
                decoration: InputDecoration(
                  labelText: 'Video tili',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                  filled: true,
                  fillColor: theme.colorScheme.surface,
                ),
                items: const [
                  DropdownMenuItem(value: 'auto', child: Text('Avtomatik')),
                  DropdownMenuItem(value: 'en', child: Text('Ingliz')),
                  DropdownMenuItem(value: 'ru', child: Text('Rus')),
                  DropdownMenuItem(value: 'uz', child: Text('O\'zbek')),
                  DropdownMenuItem(value: 'tr', child: Text('Turk')),
                  DropdownMenuItem(value: 'kk', child: Text('Qozoq')),
                  DropdownMenuItem(value: 'tg', child: Text('Tojik')),
                  DropdownMenuItem(value: 'ky', child: Text('Qirg\'iz')),
                ],
                onChanged: isRunning ? null : (v) {
                  if (v != null) onSourceLangChanged(v);
                },
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: DropdownButtonFormField<String>(
                initialValue: targetLang,
                decoration: InputDecoration(
                  labelText: 'Tarjima tili',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                  filled: true,
                  fillColor: theme.colorScheme.surface,
                ),
                items: const [
                  DropdownMenuItem(value: 'uz', child: Text('O\'zbek')),
                  DropdownMenuItem(value: 'en', child: Text('Ingliz')),
                  DropdownMenuItem(value: 'ru', child: Text('Rus')),
                  DropdownMenuItem(value: 'tr', child: Text('Turk')),
                  DropdownMenuItem(value: 'kk', child: Text('Qozoq')),
                  DropdownMenuItem(value: 'tg', child: Text('Tojik')),
                  DropdownMenuItem(value: 'ky', child: Text('Qirg\'iz')),
                ],
                onChanged: isRunning ? null : (v) {
                  if (v != null) onTargetLangChanged(v);
                },
              ),
            ),
          ],
        ),
        if (_videoModes.contains(mode)) ...[
          const SizedBox(height: 14),
          _AppearanceRow(
            appearance: appearance,
            enabled: !isRunning,
            onChanged: onAppearanceChanged,
          ),
        ],
        Expanded(
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            child: _ModePreview(key: ValueKey(mode), mode: mode),
          ),
        ),
      ],
    );
  }
}

/// Compact row for subtitle appearance (font size / position / colour).
class _AppearanceRow extends StatelessWidget {
  const _AppearanceRow({
    required this.appearance,
    required this.enabled,
    required this.onChanged,
  });

  final AppearanceSettings appearance;
  final bool enabled;
  final ValueChanged<AppearanceSettings> onChanged;

  static const _colors = {
    '#FFE680': 'Sariq',
    '#FFFFFF': 'Oq',
    '#7DD3FC': 'Ko\'k',
    '#A7F3D0': 'Yashil',
  };

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _MiniDropdown<double>(
            label: 'Shrift',
            value: appearance.fontScale,
            items: {0.85: 'Kichik', 1.0: 'O\'rta', 1.2: 'Katta'},
            enabled: enabled,
            onChanged: (v) => onChanged(appearance.copyWith(fontScale: v)),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _MiniDropdown<String>(
            label: 'Joyi',
            value: appearance.position,
            items: const {'bottom': 'Past', 'top': 'Tepa'},
            enabled: enabled,
            onChanged: (v) => onChanged(appearance.copyWith(position: v)),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: _MiniDropdown<String>(
            label: 'Rang',
            value: _colors.containsKey(appearance.subColor) ? appearance.subColor : '#FFE680',
            items: _colors,
            enabled: enabled,
            onChanged: (v) => onChanged(appearance.copyWith(subColor: v)),
          ),
        ),
      ],
    );
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
        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
      ),
      items: [
        for (final e in items.entries)
          DropdownMenuItem(value: e.key, child: Text(e.value)),
      ],
      onChanged: enabled ? (v) { if (v != null) onChanged(v); } : null,
    );
  }
}

class _ModePreview extends StatelessWidget {
  final String mode;
  const _ModePreview({super.key, required this.mode});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    Widget content;
    switch (mode) {
      case 'dual_vocab':
      case 'original_vocab':
      case 'dual':
      case 'original':
        final hasVocab = mode.contains('vocab');
        final isDual = mode.startsWith('dual');
        
        content = Container(
          width: double.infinity,
          height: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFF222222)),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFF1A1A1A),
                Color(0xFF0A0A0A),
              ],
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
                    const Text('This is the original text', textAlign: TextAlign.center, style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold, shadows: [Shadow(blurRadius: 4, color: Colors.black)])),
                    if (isDual)
                      const Text('Bu tarjima qilingan matn', textAlign: TextAlign.center, style: TextStyle(color: Color(0xFFFFE680), fontSize: 13, fontWeight: FontWeight.bold, shadows: [Shadow(blurRadius: 4, color: Colors.black)])),
                  ],
                ),
              ),
            ],
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
            color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: theme.colorScheme.outlineVariant, style: BorderStyle.solid),
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  mode == 'all' ? Icons.all_inclusive_rounded : Icons.description_rounded, 
                  size: 36, 
                  color: theme.colorScheme.primary.withValues(alpha: 0.7)
                ),
                const SizedBox(height: 12),
                Text(
                  mode == 'all' ? 'Barcha fayllar (Video, Matn, Lug\'at, SRT)' : 'Faqat hujjat fayllari yaratiladi',
                  style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
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
        const SizedBox(height: 24),
        Text(
          'Namuna',
          style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600, color: theme.colorScheme.primary),
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
            TextSpan(text: '$en - ', style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600, shadows: [Shadow(blurRadius: 3)])),
            TextSpan(text: uz, style: const TextStyle(color: Color(0xFF7DD3FC), fontSize: 13, fontWeight: FontWeight.w500, shadows: [Shadow(blurRadius: 3)])),
          ],
        ),
      ),
    );
  }
}

