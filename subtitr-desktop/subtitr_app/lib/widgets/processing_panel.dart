import 'package:flutter/material.dart';
import '../services/desktop_processor_service.dart';

class ProcessingPanel extends StatelessWidget {
  const ProcessingPanel({
    super.key,
    required this.selectedName,
    required this.selectedPath,
    required this.outDir,
    required this.isRunning,
    required this.progress,
    required this.status,
    required this.result,
    this.estimatedSeconds = 0,
    this.estimateText = '',
    this.startTime,
    required this.onStart,
    this.onReview,
    this.onCancel,
    this.onStartBatch,
    this.videoCount = 0,
    required this.onOpenPath,
  });

  final String selectedName;
  final String selectedPath;
  final String outDir;
  final bool isRunning;
  final double progress;
  final String status;
  final ProcessorResult? result;
  final int estimatedSeconds;
  final String estimateText;
  final DateTime? startTime;
  final VoidCallback onStart;
  final VoidCallback? onReview;
  final VoidCallback? onCancel;
  final VoidCallback? onStartBatch;
  final int videoCount;
  final Future<void> Function(String path) onOpenPath;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final canRun = !isRunning && selectedPath.isNotEmpty;

    String timeText = '';
    if (isRunning && startTime != null && progress > 0.05) {
      final elapsed = DateTime.now().difference(startTime!).inSeconds;
      final totalEst = elapsed / progress;
      final rem = (totalEst - elapsed).clamp(0, 9999).toInt();
      final m = rem ~/ 60;
      final s = rem % 60;
      timeText = 'Qolgan vaqt: ${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
    } else if (isRunning && startTime != null) {
      timeText = 'Hisoblanmoqda...';
    } else if (!isRunning && estimatedSeconds > 0 && result == null) {
      final m = estimatedSeconds ~/ 60;
      final s = estimatedSeconds % 60;
      timeText = 'Taxminiy vaqt: ${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
    }

    final content = Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        if (timeText.isNotEmpty) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.timer_outlined, size: 18, color: theme.colorScheme.onSurfaceVariant),
                const SizedBox(width: 8),
                Text(
                  timeText,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],
        if (!isRunning && result == null && estimateText.isNotEmpty) ...[
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.data_usage_rounded, size: 16, color: theme.colorScheme.onSurfaceVariant),
              const SizedBox(width: 6),
              Text(
                estimateText,
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant),
              ),
            ],
          ),
          const SizedBox(height: 16),
        ],
        if (isRunning || progress > 0) ...[
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: theme.colorScheme.surfaceContainerHighest,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Text(
                  status,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${(progress * 100).round()}%',
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
        ] else if (status.isNotEmpty && status != 'Tayyor' && status != 'Kinolar papkasiga video tashlang') ...[
          const SizedBox(height: 8),
          Text(
            status,
            style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
          const SizedBox(height: 24),
        ],
        
        Wrap(
          spacing: 16,
          runSpacing: 16,
          alignment: WrapAlignment.center,
          children: [
            if (isRunning && onCancel != null)
              FilledButton.icon(
                onPressed: onCancel,
                icon: const Icon(Icons.stop_rounded),
                label: const Text('To\'xtatish'),
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xFFB00020),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 20),
                  textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
              )
            else
              FilledButton.icon(
                onPressed: canRun ? onStart : null,
                icon: const Icon(Icons.auto_awesome_rounded),
                label: const Text('Boshlash'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 20),
                  textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
              ),
            if (!isRunning && onReview != null)
              OutlinedButton.icon(
                onPressed: canRun ? onReview : null,
                icon: const Icon(Icons.edit_note_rounded),
                label: const Text('Ko\'rib chiqib render'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                ),
              ),
            if (!isRunning && onStartBatch != null && videoCount > 1)
              OutlinedButton.icon(
                onPressed: onStartBatch,
                icon: const Icon(Icons.playlist_play_rounded),
                label: Text('Barchasini ($videoCount)'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                ),
              ),
            OutlinedButton.icon(
              onPressed: outDir.isEmpty ? null : () => onOpenPath(outDir),
              icon: const Icon(Icons.folder_copy_rounded),
              label: const Text('Natijalar'),
            ),
            OutlinedButton.icon(
              onPressed: selectedPath.isEmpty ? null : () => onOpenPath(selectedPath),
              icon: const Icon(Icons.play_arrow_rounded),
              label: const Text('Videoni ochish'),
            ),
          ],
        ),
        
        if (result != null) ...[
          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 24),
          _ResultView(result: result!, onOpen: onOpenPath),
        ],
      ],
    );

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxHeight.isInfinite) {
          return content;
        }
        return SingleChildScrollView(
          child: Container(
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(vertical: 24),
            constraints: BoxConstraints(
              minHeight: constraints.maxHeight,
            ),
            child: content,
          ),
        );
      },
    );
  }
}

class _ResultView extends StatelessWidget {
  const _ResultView({required this.result, required this.onOpen});

  final ProcessorResult result;
  final Future<void> Function(String path) onOpen;

  IconData _iconFor(String kind) {
    return switch (kind) {
      'video' => Icons.movie_rounded,
      'docx' => Icons.article_rounded,
      'txt' => Icons.text_snippet_rounded,
      'srt' => Icons.subtitles_rounded,
      'ass' => Icons.closed_caption_rounded,
      _ => Icons.insert_drive_file_rounded,
    };
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Tayyor fayllar',
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          'Transkripsiya: ${result.transcriber}  •  Tarjima: ${result.translator}',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 12),
        for (final output in result.outputs)
          Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Material(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(10),
              clipBehavior: Clip.antiAlias,
              child: ListTile(
                dense: true,
                leading: Icon(_iconFor(output.kind), color: theme.colorScheme.primary),
                title: Text(
                  output.label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                subtitle: Text(
                  output.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: IconButton(
                  tooltip: 'Ochish',
                  onPressed: () => onOpen(output.path),
                  icon: const Icon(Icons.open_in_new_rounded, size: 20),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
