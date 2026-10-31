import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

import 'subtitle_player.dart' show playerAvailable;

/// Tayyor yoki tanlangan videolarni tashqi ilovalarsiz (VLC, mpv va h.k.)
/// to'g'ridan-to'g'ri ilovaning o'zida tomosha qilish uchun zamonaviy
/// o'rnatilgan video pleyer modali.
class InAppVideoPlayerDialog extends StatefulWidget {
  const InAppVideoPlayerDialog({
    super.key,
    required this.videoPath,
    this.subtitlePath,
    this.title,
    this.onOpenExternal,
  });

  final String videoPath;
  final String? subtitlePath;
  final String? title;
  final VoidCallback? onOpenExternal;

  /// Pleyer mavjud bo'lsa modal oynada ochadi, aks holda tashqi ochishga yo'naltiradi.
  static Future<void> show(
    BuildContext context, {
    required String videoPath,
    String? subtitlePath,
    String? title,
    Future<void> Function(String path)? onOpenExternal,
  }) async {
    if (!playerAvailable) {
      if (onOpenExternal != null) {
        await onOpenExternal(videoPath);
      }
      return;
    }

    await showDialog<void>(
      context: context,
      barrierDismissible: true,
      barrierColor: Colors.black.withValues(alpha: 0.85),
      builder: (ctx) => InAppVideoPlayerDialog(
        videoPath: videoPath,
        subtitlePath: subtitlePath,
        title: title,
        onOpenExternal: onOpenExternal == null ? null : () => onOpenExternal(videoPath),
      ),
    );
  }

  @override
  State<InAppVideoPlayerDialog> createState() => _InAppVideoPlayerDialogState();
}

class _InAppVideoPlayerDialogState extends State<InAppVideoPlayerDialog> {
  Player? _player;
  VideoController? _video;
  bool _ready = false;
  String? _error;

  String get _displayName {
    if (widget.title != null && widget.title!.isNotEmpty) {
      return widget.title!;
    }
    return File(widget.videoPath).uri.pathSegments.last;
  }

  bool get _hasSubtitles {
    final sub = widget.subtitlePath;
    return sub != null && sub.isNotEmpty && File(sub).existsSync();
  }

  @override
  void initState() {
    super.initState();
    _initPlayer();
  }

  Future<void> _initPlayer() async {
    try {
      final player = Player();
      final video = VideoController(player);

      await player.open(
        Media(Uri.file(widget.videoPath).toString()),
        play: true,
      );

      if (_hasSubtitles) {
        await player.setSubtitleTrack(
          SubtitleTrack.uri(Uri.file(widget.subtitlePath!).toString()),
        );
      }

      if (!mounted) {
        await player.dispose();
        return;
      }

      setState(() {
        _player = player;
        _video = video;
        _ready = true;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    }
  }

  @override
  void dispose() {
    _player?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final size = MediaQuery.sizeOf(context);
    final dialogWidth = (size.width * 0.88).clamp(600.0, 1280.0);
    final dialogHeight = (size.height * 0.88).clamp(420.0, 850.0);

    return CallbackShortcuts(
      bindings: {
        const SingleActivator(LogicalKeyboardKey.escape): () {
          Navigator.of(context).pop();
        },
      },
      child: Focus(
        autofocus: true,
        child: Dialog(
          backgroundColor: const Color(0xFF0A0A0A),
          insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF222222)),
          ),
          clipBehavior: Clip.antiAlias,
          child: SizedBox(
            width: dialogWidth,
            height: dialogHeight,
            child: Column(
              children: [
                // Yuqori sarlavha paneli
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: const BoxDecoration(
                    color: Color(0xFF111111),
                    border: Border(
                      bottom: BorderSide(color: Color(0xFF222222)),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.movie_filter_rounded,
                        color: Colors.white,
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _displayName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      if (_hasSubtitles) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(
                              color: Colors.white.withValues(alpha: 0.2),
                            ),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.subtitles_rounded,
                                size: 14,
                                color: Colors.amberAccent,
                              ),
                              SizedBox(width: 4),
                              Text(
                                "Subtitr ulangan",
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500,
                                  color: Colors.amberAccent,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(width: 12),
                      if (widget.onOpenExternal != null)
                        IconButton(
                          tooltip: "Tashqi pleyerda ochish (VLC / mpv)",
                          onPressed: () {
                            _player?.pause();
                            widget.onOpenExternal!();
                          },
                          icon: const Icon(Icons.open_in_new_rounded, size: 18),
                        ),
                      IconButton(
                        tooltip: "Yopish (Esc)",
                        onPressed: () => Navigator.of(context).pop(),
                        icon: const Icon(Icons.close_rounded, size: 20),
                      ),
                    ],
                  ),
                ),

                // Video maydoni
                Expanded(
                  child: Container(
                    color: Colors.black,
                    child: _buildBody(),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.error_outline_rounded,
                color: Colors.redAccent,
                size: 48,
              ),
              const SizedBox(height: 16),
              const Text(
                "Videoni o'rnatilgan pleyerda ochib bo'lmadi",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey, fontSize: 13),
              ),
              const SizedBox(height: 20),
              if (widget.onOpenExternal != null)
                FilledButton.icon(
                  onPressed: widget.onOpenExternal,
                  icon: const Icon(Icons.open_in_new_rounded, size: 16),
                  label: const Text("Tashqi ilovada ochish"),
                ),
            ],
          ),
        ),
      );
    }

    if (!_ready || _video == null) {
      return const Center(
        child: SizedBox(
          width: 32,
          height: 32,
          child: CircularProgressIndicator(strokeWidth: 2.5),
        ),
      );
    }

    return Video(
      controller: _video!,
      controls: AdaptiveVideoControls,
    );
  }
}
