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

  static const _videoModes = {'dual_vocab', 'original_vocab', 'dual', 'original', 'translated'};

  /// Rejimlar ro'yxati, "Video" va "Hujjat" sarlavhalari bilan.
  ///
  /// Sarlavhalar tanlanmaydigan (`enabled: false`) element sifatida
  /// qo'shiladi — ularning qiymati hech qachon rejim qiymatiga teng
  /// bo'lmaydi, shuning uchun tanlovga xalaqit qilmaydi.
  List<DropdownMenuItem<String>> _modeItems(ThemeData theme) {
    final video = modes.where((m) => _videoModes.contains(m.value));
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
              // Uzun nom tor oynada chetidan toshib ketmasin.
              Expanded(
                child: Text(m.title, overflow: TextOverflow.ellipsis),
              ),
            ],
          ),
        );

    return [
      if (video.isNotEmpty) header('Video'),
      for (final m in video) entry(m),
      if (docs.isNotEmpty) header('Hujjat'),
      for (final m in docs) entry(m),
    ];
  }

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
          // Ro'yxat uzun (9 ta) — "Video" va "Hujjat" deb ikkiga bo'linadi.
          isExpanded: true,
          items: _modeItems(theme),
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
                isExpanded: true,
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
                isExpanded: true,
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
            // "Faqat tarjima" da asl matn ko'rinmaydi, demak uning uslubini
            // so'rashning ma'nosi yo'q.
            showOrigStyle: mode != 'translated',
          ),
        ],
        Expanded(
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 300),
            child: _ModePreview(
              key: ValueKey('$mode|${appearance.subColor}|${appearance.origStyle}'),
              mode: mode,
              subColor: appearance.subColor,
              origStyle: appearance.origStyle,
            ),
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
    this.showOrigStyle = true,
  });

  final AppearanceSettings appearance;
  final bool enabled;
  final ValueChanged<AppearanceSettings> onChanged;
  final bool showOrigStyle;

  // Yorqin, to'yingan ranglar: oldingi och (pastel) ohanglar kuydirilgandan
  // keyin ekranda xira ko'rinardi.
  static const _colors = {
    '#39FF14': 'Neon yashil',
    '#FFE680': 'Sariq',
    '#FFFFFF': 'Oq',
    '#00E5FF': 'Ko\'k',
    '#FF2D95': 'Pushti',
  };

  @override
  Widget build(BuildContext context) {
    // Ikki qator: bitta qatorga oltita ro'yxat sig'maydi.
    return Column(
      children: [
        Row(children: _rowOne()),
        const SizedBox(height: 10),
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
            items: const {false: 'Yo\'q', true: 'Ha'},
            enabled: enabled,
            onChanged: (v) => onChanged(appearance.copyWith(upscale: v)),
          ),
        ),
        const SizedBox(width: 10),
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
          const SizedBox(width: 10),
        ],
        Expanded(
          child: _MiniDropdown<String>(
            label: 'Rang',
            value: _colors.containsKey(appearance.subColor) ? appearance.subColor : '#39FF14',
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
  final String subColor;
  final String origStyle;
  const _ModePreview({
    super.key,
    required this.mode,
    this.subColor = '#39FF14',
    this.origStyle = 'box',
  });

  /// "#RRGGBB" -> Color (noto'g'ri qiymatda neon yashilga qaytadi).
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
                    if (showOriginal)
                      if (origStyle == 'box')
                        Container(
                          color: const Color(0xFFFFD400),
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          child: const Text('This is the original text', textAlign: TextAlign.center, style: TextStyle(color: Colors.black, fontSize: 13, fontWeight: FontWeight.w900)),
                        )
                      else
                        const Text('This is the original text', textAlign: TextAlign.center, style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w900, shadows: [Shadow(blurRadius: 4, color: Colors.black)])),
                    if (isDual)
                      Text('Bu tarjima qilingan matn', textAlign: TextAlign.center, style: TextStyle(color: _subColor, fontSize: showOriginal ? 13 : 15, fontWeight: FontWeight.w900, shadows: const [Shadow(blurRadius: 4, color: Colors.black)])),
                  ],
                ),
              ),
            ],
          ),
        );
        break;
      case 'reading':
        // Namuna: kitob sahifasiga o'xshash maket — foydalanuvchi nima
        // olishini tanlashdan oldin ko'radi.
        content = Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: theme.colorScheme.outlineVariant),
          ),
          child: Center(
            child: AspectRatio(
              aspectRatio: 1 / 1.414, // A4
              child: Container(
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
                    const _PaperLine(widthFactor: 0.72, height: 5, color: Color(0xFF15171A)),
                    const SizedBox(height: 5),
                    const _PaperLine(widthFactor: 0.36, height: 2.5, color: Color(0xFFB4B9C2)),
                    const SizedBox(height: 7),
                    Container(height: 0.6, color: const Color(0xFFD7DAE0)),
                    const SizedBox(height: 8),
                    // Abzatslar: oxirgi qatori kalta — haqiqiy matndek.
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
            TextSpan(text: en, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w900, shadows: [Shadow(blurRadius: 3, color: Colors.black)])),
            const TextSpan(text: '  ·  ', style: TextStyle(color: Color(0xFF8A93A6), fontSize: 13, fontWeight: FontWeight.w900)),
            TextSpan(text: uz, style: TextStyle(color: _subColor, fontSize: 13, fontWeight: FontWeight.w900, shadows: const [Shadow(blurRadius: 3, color: Colors.black)])),
          ],
        ),
      ),
    );
  }
}

/// Namunadagi "matn qatori" — bir dona kulrang chiziq.
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
