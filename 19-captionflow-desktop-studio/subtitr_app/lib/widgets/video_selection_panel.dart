import 'dart:io';
import 'package:flutter/material.dart';
import '../services/desktop_processor_service.dart';

class VideoSelectionPanel extends StatelessWidget {
  const VideoSelectionPanel({
    super.key,
    required this.kinoDir,
    required this.currentDir,
    required this.videos,
    required this.selectedVideo,
    required this.externalVideoPath,
    required this.isRunning,
    required this.isLoading,
    required this.onScan,
    required this.onPickExternal,
    required this.onSelectVideo,
    required this.onClearExternal,
    required this.onNavigateBack,
    required this.onUrlSubmit,
    required this.onDownloadOnly,
  });

  final String kinoDir;
  final String? currentDir;
  final List<DesktopVideo> videos;
  final DesktopVideo? selectedVideo;
  final String? externalVideoPath;
  final bool isRunning;
  final bool isLoading;
  final VoidCallback onScan;
  final VoidCallback onPickExternal;
  final ValueChanged<DesktopVideo> onSelectVideo;
  final VoidCallback onClearExternal;
  final VoidCallback onNavigateBack;
  final ValueChanged<String> onUrlSubmit;
  final ValueChanged<String> onDownloadOnly;

  String get _selectedName {
    final p = externalVideoPath;
    if (p != null) {
      if (p.startsWith('http')) return 'Havola (yuklab olinadi)';
      return File(p).uri.pathSegments.last;
    }
    return selectedVideo?.name ?? 'Video tanlanmagan';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: isRunning ? null : onPickExternal,
            icon: const Icon(Icons.add_to_drive_rounded),
            label: const Text('Video tanlash (Fayldan)'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
        const SizedBox(height: 10),
        const Row(
          children: [
            Expanded(child: Divider()),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: Text('yoki'),
            ),
            Expanded(child: Divider()),
          ],
        ),
        const SizedBox(height: 10),
        _UrlInput(
          enabled: !isRunning,
          onSubmit: onUrlSubmit,
          onDownloadOnly: onDownloadOnly,
        ),
        const SizedBox(height: 16),
        if (externalVideoPath != null)
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withValues(alpha: 0.4),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: theme.colorScheme.primary.withValues(alpha: 0.2),
              ),
            ),
            child: Row(
              children: [
                Icon(Icons.video_file_rounded, color: theme.colorScheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_selectedName, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600)),
                      const SizedBox(height: 2),
                      Text(
                        externalVideoPath!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: 'Olib tashlash',
                  onPressed: isRunning ? null : onClearExternal,
                  icon: const Icon(Icons.close_rounded, size: 20),
                  style: IconButton.styleFrom(
                    padding: const EdgeInsets.all(4),
                    minimumSize: const Size(32, 32),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

/// URL input for downloading a video from YouTube / Instagram / any site.
/// When a valid URL is entered, two actions appear: download only, or
/// download + subtitle.
class _UrlInput extends StatefulWidget {
  const _UrlInput({
    required this.enabled,
    required this.onSubmit,
    required this.onDownloadOnly,
  });

  final bool enabled;
  final ValueChanged<String> onSubmit;
  final ValueChanged<String> onDownloadOnly;

  @override
  State<_UrlInput> createState() => _UrlInputState();
}

class _UrlInputState extends State<_UrlInput> {
  final TextEditingController _controller = TextEditingController();
  bool _hasUrl = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String? get _url {
    final url = _controller.text.trim();
    return url.startsWith('http') ? url : null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: _controller,
          enabled: widget.enabled,
          keyboardType: TextInputType.url,
          onChanged: (v) {
            final has = v.trim().startsWith('http');
            if (has != _hasUrl) setState(() => _hasUrl = has);
          },
          decoration: InputDecoration(
            hintText: 'YouTube / Instagram / kino sayti havolasi',
            prefixIcon: const Icon(Icons.link_rounded, size: 20),
            isDense: true,
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
        if (_hasUrl) ...[
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: widget.enabled ? () { final u = _url; if (u != null) widget.onDownloadOnly(u); } : null,
                  icon: const Icon(Icons.file_download_outlined, size: 18),
                  label: const Text('Videoni yuklash'),
                  style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: FilledButton.icon(
                  onPressed: widget.enabled ? () { final u = _url; if (u != null) widget.onSubmit(u); } : null,
                  icon: const Icon(Icons.auto_awesome_rounded, size: 18),
                  label: const Text('Yuklab + yozish'),
                  style: FilledButton.styleFrom(
                    backgroundColor: theme.colorScheme.primary,
                    foregroundColor: theme.colorScheme.onPrimary,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                ),
              ),
            ],
          ),
        ],
      ],
    );
  }
}
