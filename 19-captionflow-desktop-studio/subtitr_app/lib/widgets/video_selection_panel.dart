import 'dart:io';
import 'package:flutter/material.dart';
import '../services/desktop_processor_service.dart';

class VideoSelectionPanel extends StatefulWidget {
  const VideoSelectionPanel({
    super.key,
    required this.kinoDir,
    required this.currentDir,
    required this.videos,
    required this.selectedVideo,
    required this.externalVideoPath,
    required this.externalSubtitlePath,
    required this.subtitleOffset,
    required this.isRunning,
    required this.isLoading,
    required this.onScan,
    required this.onPickExternal,
    required this.onPickSubtitle,
    required this.onClearSubtitle,
    required this.onOffsetChanged,
    required this.onSelectVideo,
    required this.onClearExternal,
    required this.onNavigateBack,
    required this.onUrlSubmit,
    required this.onDownloadOnly,
    required this.onPlaylistSubmit,
    this.onPreviewVideo,
  });

  final String kinoDir;
  final String? currentDir;
  final List<DesktopVideo> videos;
  final DesktopVideo? selectedVideo;
  final String? externalVideoPath;
  final String? externalSubtitlePath;
  final double subtitleOffset;
  final bool isRunning;
  final bool isLoading;
  final VoidCallback onScan;
  final VoidCallback onPickExternal;
  final VoidCallback onPickSubtitle;
  final VoidCallback onClearSubtitle;
  final ValueChanged<double> onOffsetChanged;
  final ValueChanged<DesktopVideo> onSelectVideo;
  final VoidCallback onClearExternal;
  final VoidCallback onNavigateBack;
  final ValueChanged<String> onUrlSubmit;
  final ValueChanged<String> onDownloadOnly;
  final ValueChanged<String> onPlaylistSubmit;
  final ValueChanged<String>? onPreviewVideo;

  @override
  State<VideoSelectionPanel> createState() => _VideoSelectionPanelState();
}

class _VideoSelectionPanelState extends State<VideoSelectionPanel> {
  int _selectedSourceTab = 0; // 0: Fayllar va Katalog, 1: Internet (URL)

  String get _selectedName {
    final p = widget.externalVideoPath;
    if (p != null) {
      if (p.startsWith('http')) return 'Havola (yuklab olinadi)';
      return File(p).uri.pathSegments.last;
    }
    return widget.selectedVideo?.name ?? 'Video tanlanmagan';
  }

  String? get _effectiveVideoPath =>
      widget.externalVideoPath ?? widget.selectedVideo?.path;

  static String _formatSize(int bytes) {
    if (bytes <= 0) return '';
    if (bytes >= 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
    }
    return '${(bytes / (1024 * 1024)).toStringAsFixed(0)} MB';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activePath = _effectiveVideoPath;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 1. Manba tanlash (Katalog yoki URL)
        Container(
          padding: const EdgeInsets.all(4),
          decoration: BoxDecoration(
            color: const Color(0xFF141414),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFF262626)),
          ),
          child: Row(
            children: [
              Expanded(
                child: _SourceTabButton(
                  title: 'Kompyuterdan / Papka',
                  icon: Icons.folder_rounded,
                  isSelected: _selectedSourceTab == 0,
                  onTap: () => setState(() => _selectedSourceTab = 0),
                ),
              ),
              const SizedBox(width: 4),
              Expanded(
                child: _SourceTabButton(
                  title: 'Internetdan (URL)',
                  icon: Icons.link_rounded,
                  isSelected: _selectedSourceTab == 1,
                  onTap: () => setState(() => _selectedSourceTab = 1),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // 2. Tab mazmuni
        if (_selectedSourceTab == 0) ...[
          // Fayl tanlash tugmasi
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: widget.isRunning ? null : widget.onPickExternal,
              icon: const Icon(Icons.add_to_drive_rounded),
              label: const Text('Istalgan videoni tanlash (Fayldan)'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ),
          const SizedBox(height: 10),

          // Skanerlangan videolar ro'yxati (Katalog ~/Videos)
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFF0F0F0F),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF222222)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: Row(
                    children: [
                      const Icon(Icons.video_library_rounded, size: 16, color: Color(0xFFAAAAAA)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          widget.currentDir != null && widget.currentDir != widget.kinoDir
                              ? File(widget.currentDir!).uri.pathSegments.reversed.skip(1).firstOrNull ?? 'Papka'
                              : 'Kinolar papkasi (~/Videos)',
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFFCCCCCC)),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (widget.currentDir != null && widget.kinoDir != widget.currentDir)
                        IconButton(
                          tooltip: 'Yuqoriga (Orqaga)',
                          icon: const Icon(Icons.arrow_upward_rounded, size: 16),
                          visualDensity: VisualDensity.compact,
                          onPressed: widget.isRunning ? null : widget.onNavigateBack,
                        ),
                      IconButton(
                        tooltip: 'Qayta skanerlash',
                        icon: const Icon(Icons.refresh_rounded, size: 16),
                        visualDensity: VisualDensity.compact,
                        onPressed: widget.isRunning ? null : widget.onScan,
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1, color: Color(0xFF222222)),
                if (widget.isLoading)
                  const Padding(
                    padding: EdgeInsets.all(20),
                    child: Center(
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                  )
                else if (widget.videos.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                    child: Center(
                      child: Text(
                        "Ushbu papkada video topilmadi.\nYuqoridagi tugma orqali istalgan videoni tanlang.",
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 12, color: Color(0xFF777777)),
                      ),
                    ),
                  )
                else
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 180),
                    child: ListView.separated(
                      shrinkWrap: true,
                      itemCount: widget.videos.length,
                      separatorBuilder: (_, _) => const Divider(height: 1, color: Color(0xFF1A1A1A)),
                      itemBuilder: (context, index) {
                        final v = widget.videos[index];
                        final isSelected = activePath == v.path;
                        return InkWell(
                          onTap: widget.isRunning ? null : () => widget.onSelectVideo(v),
                          child: Container(
                            color: isSelected ? const Color(0xFF1E293B) : null,
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            child: Row(
                              children: [
                                Icon(
                                  v.isDir ? Icons.folder_rounded : Icons.movie_outlined,
                                  size: 18,
                                  color: v.isDir
                                      ? const Color(0xFFFFD400)
                                      : (isSelected ? const Color(0xFF38BDF8) : const Color(0xFF888888)),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    v.name,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                                      color: isSelected ? Colors.white : const Color(0xFFDDDDDD),
                                    ),
                                  ),
                                ),
                                if (v.subtitleName.isNotEmpty) ...[
                                  const SizedBox(width: 6),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF0284C7).withValues(alpha: 0.3),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: const Text(
                                      'SRT',
                                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF38BDF8)),
                                    ),
                                  ),
                                ],
                                if (v.size > 0) ...[
                                  const SizedBox(width: 8),
                                  Text(
                                    _formatSize(v.size),
                                    style: const TextStyle(fontSize: 11, color: Color(0xFF777777)),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        );
                      },
                    ),
                  ),
              ],
            ),
          ),
        ] else ...[
          // Internet URL kiritish
          _UrlInput(
            enabled: !widget.isRunning,
            onSubmit: widget.onUrlSubmit,
            onDownloadOnly: widget.onDownloadOnly,
            onPlaylistSubmit: widget.onPlaylistSubmit,
          ),
        ],

        const SizedBox(height: 14),

        // 3. Tashqi subtitr import qilish
        OutlinedButton.icon(
          onPressed: widget.isRunning ? null : widget.onPickSubtitle,
          icon: const Icon(Icons.subtitles_outlined),
          label: Text(widget.externalSubtitlePath == null ? 'Tashqi SRT/ASS import qilish' : 'Subtitrni almashtirish'),
        ),
        if (widget.externalSubtitlePath != null) ...[
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: Text(File(widget.externalSubtitlePath!).uri.pathSegments.last, maxLines: 1, overflow: TextOverflow.ellipsis)),
            IconButton(tooltip: 'Subtitrni olib tashlash', onPressed: widget.isRunning ? null : widget.onClearSubtitle, icon: const Icon(Icons.close_rounded)),
          ]),
          const SizedBox(height: 4),
          Row(children: [
            const Text('Vaqt siljishi:'),
            const SizedBox(width: 12),
            Expanded(child: DropdownButton<double>(
              isExpanded: true,
              value: widget.subtitleOffset,
              items: const [-10.0, -5.0, -2.0, 0.0, 2.0, 5.0, 10.0].map((v) => DropdownMenuItem(value: v, child: Text('${v >= 0 ? '+' : ''}$v soniya'))).toList(),
              onChanged: widget.isRunning ? null : (v) { if (v != null) widget.onOffsetChanged(v); },
            )),
          ]),
        ],

        // 4. Faol tanlangan video kartasi
        if (activePath != null && activePath.isNotEmpty) ...[
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: theme.colorScheme.primary.withValues(alpha: 0.25),
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
                      Text(
                        _selectedName,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13.5),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        activePath,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                if (!activePath.startsWith('http') && widget.onPreviewVideo != null) ...[
                  IconButton(
                    tooltip: "Videoni ko'rish",
                    onPressed: widget.isRunning
                        ? null
                        : () => widget.onPreviewVideo!(activePath),
                    icon: const Icon(Icons.play_circle_outline_rounded, size: 20),
                    style: IconButton.styleFrom(
                      padding: const EdgeInsets.all(4),
                      minimumSize: const Size(32, 32),
                    ),
                  ),
                ],
                IconButton(
                  tooltip: 'Olib tashlash',
                  onPressed: widget.isRunning ? null : widget.onClearExternal,
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
      ],
    );
  }
}

class _SourceTabButton extends StatelessWidget {
  const _SourceTabButton({
    required this.title,
    required this.icon,
    required this.isSelected,
    required this.onTap,
  });

  final String title;
  final IconData icon;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(9),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF262626) : Colors.transparent,
          borderRadius: BorderRadius.circular(9),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: isSelected ? Colors.white : const Color(0xFF888888)),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  color: isSelected ? Colors.white : const Color(0xFF888888),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// URL input for downloading a video from YouTube / Instagram / any site.
class _UrlInput extends StatefulWidget {
  const _UrlInput({
    required this.enabled,
    required this.onSubmit,
    required this.onDownloadOnly,
    required this.onPlaylistSubmit,
  });

  final bool enabled;
  final ValueChanged<String> onSubmit;
  final ValueChanged<String> onDownloadOnly;
  final ValueChanged<String> onPlaylistSubmit;

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
    final raw = _controller.text.trim();
    if (raw.isEmpty) return null;
    if (raw.startsWith('http://') || raw.startsWith('https://')) return raw;
    if (raw.contains('.') && !raw.contains(' ')) return 'https://$raw';
    return null;
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
            final raw = v.trim();
            final has = raw.startsWith('http') || (raw.contains('.') && !raw.contains(' '));
            if (has != _hasUrl) setState(() => _hasUrl = has);
          },
          decoration: InputDecoration(
            hintText: 'YouTube / Instagram / havola kiriting',
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
                  label: const Text('Faqat yuklash'),
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
          const SizedBox(height: 8),
          TextButton.icon(
            onPressed: widget.enabled ? () { final u = _url; if (u != null) widget.onPlaylistSubmit(u); } : null,
            icon: const Icon(Icons.playlist_add_rounded, size: 18),
            label: const Text('Playlist yoki kanalni tanlab navbatga qo\'shish'),
          ),
        ],
      ],
    );
  }
}
