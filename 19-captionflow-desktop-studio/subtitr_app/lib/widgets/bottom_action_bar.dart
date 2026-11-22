import 'package:flutter/material.dart';

class BottomActionBar extends StatelessWidget {
  const BottomActionBar({
    super.key,
    required this.sourceLang,
    required this.targetLang,
    required this.isRunning,
    required this.hasVideo,
    required this.progress,
    required this.status,
    required this.onSourceLangChanged,
    required this.onTargetLangChanged,
    required this.onStart,
    required this.onCancel,
    this.subColor = '#39FF14',
    this.startTime,
    this.estimateText = '',
  });

  final String sourceLang;
  final String targetLang;
  final bool isRunning;
  final bool hasVideo;
  final double progress;
  final String status;
  final ValueChanged<String> onSourceLangChanged;
  final ValueChanged<String> onTargetLangChanged;
  final VoidCallback onStart;
  final VoidCallback onCancel;
  final String subColor;
  final DateTime? startTime;
  final String estimateText;

  String get _timeText {
    if (isRunning && startTime != null && progress > 0.05) {
      final elapsed = DateTime.now().difference(startTime!).inSeconds;
      final totalEst = elapsed / progress;
      final rem = (totalEst - elapsed).clamp(0, 9999).toInt();
      final m = rem ~/ 60;
      final s = rem % 60;
      return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
    }
    return '';
  }

  Color get _previewColor {
    try {
      final hex = subColor.replaceFirst('#', '');
      return Color(int.parse('FF$hex', radix: 16));
    } catch (_) {
      return const Color(0xFF39FF14);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A0A),
        border: Border(
          top: BorderSide(color: Color(0xFF1A1A1A)),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Progress bar (when running)
          if (isRunning)
            LinearProgressIndicator(
              value: progress > 0.01 ? progress : null,
              minHeight: 3,
              backgroundColor: const Color(0xFF1A1A1A),
              color: const Color(0xFF2563EB),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                // Language selectors
                _CompactLangDropdown(
                  value: sourceLang,
                  items: const [
                    ('auto', 'Avto'),
                    ('en', 'EN'),
                    ('ru', 'RU'),
                    ('uz', 'UZ'),
                    ('tr', 'TR'),
                    ('kk', 'KK'),
                    ('tg', 'TG'),
                    ('ky', 'KY'),
                  ],
                  enabled: !isRunning,
                  onChanged: onSourceLangChanged,
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  child: Icon(
                    Icons.arrow_forward_rounded,
                    size: 16,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                _CompactLangDropdown(
                  value: targetLang,
                  items: const [
                    ('none', '—'),
                    ('uz', 'UZ'),
                    ('en', 'EN'),
                    ('ru', 'RU'),
                    ('tr', 'TR'),
                    ('kk', 'KK'),
                    ('tg', 'TG'),
                    ('ky', 'KY'),
                  ],
                  enabled: !isRunning,
                  onChanged: onTargetLangChanged,
                ),
                const SizedBox(width: 12),
                // Status / subtitle preview
                Expanded(
                  child: isRunning
                      ? Row(
                          children: [
                            Expanded(
                              child: Text(
                                status,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: theme.colorScheme.onSurfaceVariant,
                                ),
                              ),
                            ),
                            if (_timeText.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(left: 8),
                                child: Text(
                                  _timeText,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                    fontFamily: 'monospace',
                                    color: Color(0xFF2563EB),
                                  ),
                                ),
                              ),
                            const SizedBox(width: 8),
                            Text(
                              '${(progress * 100).round()}%',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                fontFamily: 'monospace',
                                color: Color(0xFF2563EB),
                              ),
                            ),
                          ],
                        )
                      : Text(
                          'Namuna subtitr matni shu yerda ko\'rinadi',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 12,
                            fontFamily: 'monospace',
                            color: _previewColor.withValues(alpha: 0.7),
                          ),
                        ),
                ),
                const SizedBox(width: 12),
                // Start/Cancel button
                if (isRunning)
                  FilledButton.icon(
                    onPressed: onCancel,
                    icon: const Icon(Icons.stop_rounded, size: 18),
                    label: const Text('Bekor'),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF991B1B),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 12,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  )
                else
                  FilledButton.icon(
                    onPressed: hasVideo ? onStart : null,
                    icon: const Icon(Icons.play_arrow_rounded, size: 20),
                    label: const Text('Boshlash'),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF2563EB),
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: const Color(0xFF1A1A2E),
                      disabledForegroundColor: const Color(0xFF555555),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CompactLangDropdown extends StatelessWidget {
  const _CompactLangDropdown({
    required this.value,
    required this.items,
    required this.enabled,
    required this.onChanged,
  });

  final String value;
  final List<(String, String)> items;
  final bool enabled;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 34,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF141414),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFF262626)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isDense: true,
          icon: const Icon(Icons.expand_more_rounded, size: 16),
          iconEnabledColor: const Color(0xFF71717A),
          dropdownColor: const Color(0xFF1A1A1A),
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: Colors.white,
          ),
          items: items
              .map(
                (item) => DropdownMenuItem(
                  value: item.$1,
                  child: Text(item.$2),
                ),
              )
              .toList(),
          onChanged: enabled
              ? (v) {
                  if (v != null) onChanged(v);
                }
              : null,
        ),
      ),
    );
  }
}
