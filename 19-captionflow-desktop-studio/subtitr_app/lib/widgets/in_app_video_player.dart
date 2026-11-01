import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

import 'subtitle_player.dart' show playerAvailable;

/// Tayyor yoki tanlangan videolarni alohida modal dialogda ko'rish oynasi.
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
  bool _subtitlesEnabled = true;
  Tracks _tracks = const Tracks();
  Track _track = const Track();
  StreamSubscription<Tracks>? _tracksSub;
  StreamSubscription<Track>? _trackSub;

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

  bool get _isBurnedVideo {
    final lower = widget.videoPath.toLowerCase();
    return lower.contains('_dual.') || lower.contains('_single.');
  }

  List<AudioTrack> get _realAudioTracks {
    return _tracks.audio.where((t) => t.id != 'auto' && t.id != 'no').toList();
  }

  List<SubtitleTrack> get _realSubtitleTracks {
    return _tracks.subtitle.where((t) => t.id != 'auto' && t.id != 'no').toList();
  }

  bool get _canToggleSubtitles => _hasSubtitles || _realSubtitleTracks.isNotEmpty;

  String _formatAudioTrackTitle(AudioTrack t, int index) {
    final title = t.title?.trim();
    if (title != null && title.isNotEmpty) return title;
    final lang = t.language?.trim();
    if (lang != null && lang.isNotEmpty) {
      final lower = lang.toLowerCase();
      if (lower.startsWith('uz')) return "O'zbekcha AI Dublyaj";
      if (lower.startsWith('en')) return "Asl ovoz (Original)";
      if (lower.startsWith('ru')) return "Ruscha ovoz";
      return "${lang.toUpperCase()} ovozi";
    }
    return "${index + 1}-audio trek";
  }

  String get _currentAudioLabel {
    final cur = _track.audio;
    if (cur.id == 'no') return "Ovozsiz";
    final realList = _realAudioTracks;
    final foundIdx = realList.indexWhere((t) => t.id == cur.id);
    if (foundIdx != -1) {
      return _formatAudioTrackTitle(realList[foundIdx], foundIdx);
    }
    if (realList.isNotEmpty) {
      return _formatAudioTrackTitle(realList.first, 0);
    }
    return "Audio trek";
  }

  String _formatSubtitleTrackTitle(SubtitleTrack t, int index) {
    final title = t.title?.trim();
    if (title != null && title.isNotEmpty) return title;
    final lang = t.language?.trim();
    if (lang != null && lang.isNotEmpty) {
      final lower = lang.toLowerCase();
      if (lower.startsWith('uz')) return "O'zbekcha";
      if (lower.startsWith('en')) return "Asl til (English)";
      if (lower.startsWith('ru')) return "Ruscha";
      return lang.toUpperCase();
    }
    return "${index + 1}-subtitr";
  }

  @override
  void initState() {
    super.initState();
    _subtitlesEnabled = !_isBurnedVideo;
    _initPlayer();
  }

  Future<void> _initPlayer() async {
    try {
      final player = Player();
      final video = VideoController(player);

      _tracksSub = player.stream.tracks.listen((tracks) {
        if (mounted) setState(() => _tracks = tracks);
      });
      _trackSub = player.stream.track.listen((track) {
        if (mounted) setState(() => _track = track);
      });

      await player.open(
        Media(Uri.file(widget.videoPath).toString()),
        play: true,
      );

      if (_hasSubtitles && _subtitlesEnabled) {
        await player.setSubtitleTrack(
          SubtitleTrack.uri(Uri.file(widget.subtitlePath!).toString()),
        );
      } else {
        await player.setSubtitleTrack(SubtitleTrack.no());
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

  Future<void> _toggleSubtitles() async {
    final player = _player;
    if (player == null || !_canToggleSubtitles) return;
    final nextState = !_subtitlesEnabled;
    setState(() => _subtitlesEnabled = nextState);
    try {
      if (nextState) {
        if (_hasSubtitles) {
          await player.setSubtitleTrack(
            SubtitleTrack.uri(Uri.file(widget.subtitlePath!).toString()),
          );
        } else if (_realSubtitleTracks.isNotEmpty) {
          await player.setSubtitleTrack(_realSubtitleTracks.first);
        }
      } else {
        await player.setSubtitleTrack(SubtitleTrack.no());
      }
    } catch (_) {}
  }

  Widget _buildAudioTrackSelector() {
    final realList = _realAudioTracks;
    if (realList.length <= 1) return const SizedBox.shrink();

    return PopupMenuButton<AudioTrack>(
      tooltip: "Audio trekni almashtirish (Asl ovoz / O'zbekcha AI Dublyaj)",
      initialValue: _track.audio,
      onSelected: (t) async {
        await _player?.setAudioTrack(t);
      },
      color: const Color(0xFF1E293B),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: Color(0xFF334155)),
      ),
      itemBuilder: (ctx) => [
        for (int i = 0; i < realList.length; i++)
          PopupMenuItem<AudioTrack>(
            value: realList[i],
            height: 38,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _track.audio.id == realList[i].id
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: 16,
                  color: _track.audio.id == realList[i].id
                      ? const Color(0xFF38BDF8)
                      : Colors.grey,
                ),
                const SizedBox(width: 8),
                Text(
                  _formatAudioTrackTitle(realList[i], i),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: _track.audio.id == realList[i].id
                        ? FontWeight.w700
                        : FontWeight.normal,
                    color: _track.audio.id == realList[i].id
                        ? Colors.white
                        : const Color(0xFFCBD5E1),
                  ),
                ),
              ],
            ),
          ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: const Color(0xFF38BDF8).withValues(alpha: 0.5),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.audiotrack_rounded,
              size: 14,
              color: Color(0xFF38BDF8),
            ),
            const SizedBox(width: 6),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 160),
              child: Text(
                _currentAudioLabel,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF38BDF8),
                ),
              ),
            ),
            const SizedBox(width: 4),
            const Icon(
              Icons.arrow_drop_down_rounded,
              size: 16,
              color: Color(0xFF38BDF8),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubtitleTrackSelector() {
    if (!_canToggleSubtitles) return const SizedBox.shrink();

    final realSubs = _realSubtitleTracks;
    if (realSubs.length > 1) {
      return PopupMenuButton<SubtitleTrack>(
        tooltip: "Subtitr tilini tanlash / o'chirish",
        onSelected: (st) async {
          final player = _player;
          if (player == null) return;
          if (st.id == 'no') {
            setState(() => _subtitlesEnabled = false);
            await player.setSubtitleTrack(SubtitleTrack.no());
          } else {
            setState(() => _subtitlesEnabled = true);
            await player.setSubtitleTrack(st);
          }
        },
        color: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
          side: const BorderSide(color: Color(0xFF334155)),
        ),
        itemBuilder: (ctx) => [
          PopupMenuItem<SubtitleTrack>(
            value: SubtitleTrack.no(),
            height: 38,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  !_subtitlesEnabled || _track.subtitle.id == 'no'
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: 16,
                  color: !_subtitlesEnabled || _track.subtitle.id == 'no'
                      ? Colors.amberAccent
                      : Colors.grey,
                ),
                const SizedBox(width: 8),
                const Text(
                  "Subtitrni o'chirish",
                  style: TextStyle(fontSize: 12, color: Color(0xFFCBD5E1)),
                ),
              ],
            ),
          ),
          for (int i = 0; i < realSubs.length; i++)
            PopupMenuItem<SubtitleTrack>(
              value: realSubs[i],
              height: 38,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                        ? Icons.check_circle_rounded
                        : Icons.radio_button_unchecked_rounded,
                    size: 16,
                    color: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                        ? Colors.amberAccent
                        : Colors.grey,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatSubtitleTrackTitle(realSubs[i], i),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                          ? FontWeight.w700
                          : FontWeight.normal,
                      color: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                          ? Colors.white
                          : const Color(0xFFCBD5E1),
                    ),
                  ),
                ],
              ),
            ),
        ],
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: _subtitlesEnabled
                ? Colors.amberAccent.withValues(alpha: 0.18)
                : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: _subtitlesEnabled
                  ? Colors.amberAccent.withValues(alpha: 0.5)
                  : Colors.white.withValues(alpha: 0.15),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _subtitlesEnabled
                    ? Icons.subtitles_rounded
                    : Icons.subtitles_off_rounded,
                size: 14,
                color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey,
              ),
              const SizedBox(width: 6),
              Text(
                _subtitlesEnabled ? "Subtitr: Yoqiq" : "Subtitr: O'chiq",
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey,
                ),
              ),
              const SizedBox(width: 4),
              Icon(
                Icons.arrow_drop_down_rounded,
                size: 16,
                color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey,
              ),
            ],
          ),
        ),
      );
    }

    return Tooltip(
      message: _subtitlesEnabled
          ? "Subtitrni o'chirish (ustidagi qatlamni yashirish)"
          : "Subtitrni yoqish",
      child: InkWell(
        onTap: _toggleSubtitles,
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(
            horizontal: 10,
            vertical: 5,
          ),
          decoration: BoxDecoration(
            color: _subtitlesEnabled
                ? Colors.amberAccent.withValues(alpha: 0.18)
                : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: _subtitlesEnabled
                  ? Colors.amberAccent.withValues(alpha: 0.5)
                  : Colors.white.withValues(alpha: 0.15),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _subtitlesEnabled
                    ? Icons.subtitles_rounded
                    : Icons.subtitles_off_rounded,
                size: 14,
                color: _subtitlesEnabled
                    ? Colors.amberAccent
                    : Colors.grey,
              ),
              const SizedBox(width: 6),
              Text(
                _subtitlesEnabled ? "Subtitr: Yoqiq" : "Subtitr: O'chiq",
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: _subtitlesEnabled
                      ? Colors.amberAccent
                      : Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _tracksSub?.cancel();
    _trackSub?.cancel();
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
                      _buildAudioTrackSelector(),
                      if (_realAudioTracks.length > 1) const SizedBox(width: 8),
                      _buildSubtitleTrackSelector(),
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

/// Asosiy oynaning o'ng tomonida to'g'ridan-to'g'ri integratsiya qilingan
/// video pleyer paneli (chap tomondagi sozlamalar paneli joyida qoladi).
class EmbeddedVideoPlayer extends StatefulWidget {
  const EmbeddedVideoPlayer({
    super.key,
    required this.videoPath,
    this.subtitlePath,
    this.title,
    required this.onClose,
    this.onOpenExternal,
  });

  final String videoPath;
  final String? subtitlePath;
  final String? title;
  final VoidCallback onClose;
  final ValueChanged<String>? onOpenExternal;

  @override
  State<EmbeddedVideoPlayer> createState() => _EmbeddedVideoPlayerState();
}

class _EmbeddedVideoPlayerState extends State<EmbeddedVideoPlayer> {
  Player? _player;
  VideoController? _video;
  bool _ready = false;
  String? _error;
  bool _subtitlesEnabled = true;
  Tracks _tracks = const Tracks();
  Track _track = const Track();
  StreamSubscription<Tracks>? _tracksSub;
  StreamSubscription<Track>? _trackSub;

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

  bool get _isBurnedVideo {
    final lower = widget.videoPath.toLowerCase();
    return lower.contains('_dual.') || lower.contains('_single.');
  }

  List<AudioTrack> get _realAudioTracks {
    return _tracks.audio.where((t) => t.id != 'auto' && t.id != 'no').toList();
  }

  List<SubtitleTrack> get _realSubtitleTracks {
    return _tracks.subtitle.where((t) => t.id != 'auto' && t.id != 'no').toList();
  }

  bool get _canToggleSubtitles => _hasSubtitles || _realSubtitleTracks.isNotEmpty;

  String _formatAudioTrackTitle(AudioTrack t, int index) {
    final title = t.title?.trim();
    if (title != null && title.isNotEmpty) return title;
    final lang = t.language?.trim();
    if (lang != null && lang.isNotEmpty) {
      final lower = lang.toLowerCase();
      if (lower.startsWith('uz')) return "O'zbekcha AI Dublyaj";
      if (lower.startsWith('en')) return "Asl ovoz (Original)";
      if (lower.startsWith('ru')) return "Ruscha ovoz";
      return "${lang.toUpperCase()} ovozi";
    }
    return "${index + 1}-audio trek";
  }

  String get _currentAudioLabel {
    final cur = _track.audio;
    if (cur.id == 'no') return "Ovozsiz";
    final realList = _realAudioTracks;
    final foundIdx = realList.indexWhere((t) => t.id == cur.id);
    if (foundIdx != -1) {
      return _formatAudioTrackTitle(realList[foundIdx], foundIdx);
    }
    if (realList.isNotEmpty) {
      return _formatAudioTrackTitle(realList.first, 0);
    }
    return "Audio trek";
  }

  String _formatSubtitleTrackTitle(SubtitleTrack t, int index) {
    final title = t.title?.trim();
    if (title != null && title.isNotEmpty) return title;
    final lang = t.language?.trim();
    if (lang != null && lang.isNotEmpty) {
      final lower = lang.toLowerCase();
      if (lower.startsWith('uz')) return "O'zbekcha";
      if (lower.startsWith('en')) return "Asl til (English)";
      if (lower.startsWith('ru')) return "Ruscha";
      return lang.toUpperCase();
    }
    return "${index + 1}-subtitr";
  }

  @override
  void initState() {
    super.initState();
    _subtitlesEnabled = !_isBurnedVideo;
    _initPlayer();
  }

  @override
  void didUpdateWidget(EmbeddedVideoPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.videoPath != oldWidget.videoPath ||
        widget.subtitlePath != oldWidget.subtitlePath) {
      _subtitlesEnabled = !_isBurnedVideo;
      _loadMedia();
    }
  }

  Future<void> _initPlayer() async {
    try {
      final player = Player();
      final video = VideoController(player);

      _tracksSub = player.stream.tracks.listen((tracks) {
        if (mounted) setState(() => _tracks = tracks);
      });
      _trackSub = player.stream.track.listen((track) {
        if (mounted) setState(() => _track = track);
      });

      if (!mounted) {
        await player.dispose();
        return;
      }
      setState(() {
        _player = player;
        _video = video;
      });
      await _loadMedia();
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    }
  }

  Future<void> _loadMedia() async {
    final player = _player;
    if (player == null) return;
    try {
      await player.open(
        Media(Uri.file(widget.videoPath).toString()),
        play: true,
      );
      if (_hasSubtitles && _subtitlesEnabled) {
        await player.setSubtitleTrack(
          SubtitleTrack.uri(Uri.file(widget.subtitlePath!).toString()),
        );
      } else {
        await player.setSubtitleTrack(SubtitleTrack.no());
      }
      if (mounted) {
        setState(() {
          _ready = true;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    }
  }

  Future<void> _toggleSubtitles() async {
    final player = _player;
    if (player == null || !_canToggleSubtitles) return;
    final nextState = !_subtitlesEnabled;
    setState(() => _subtitlesEnabled = nextState);
    try {
      if (nextState) {
        if (_hasSubtitles) {
          await player.setSubtitleTrack(
            SubtitleTrack.uri(Uri.file(widget.subtitlePath!).toString()),
          );
        } else if (_realSubtitleTracks.isNotEmpty) {
          await player.setSubtitleTrack(_realSubtitleTracks.first);
        }
      } else {
        await player.setSubtitleTrack(SubtitleTrack.no());
      }
    } catch (_) {}
  }

  Widget _buildAudioTrackSelector() {
    final realList = _realAudioTracks;
    if (realList.length <= 1) return const SizedBox.shrink();

    return PopupMenuButton<AudioTrack>(
      tooltip: "Audio trekni almashtirish (Asl ovoz / O'zbekcha AI Dublyaj)",
      initialValue: _track.audio,
      onSelected: (t) async {
        await _player?.setAudioTrack(t);
      },
      color: const Color(0xFF1E293B),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: Color(0xFF334155)),
      ),
      itemBuilder: (ctx) => [
        for (int i = 0; i < realList.length; i++)
          PopupMenuItem<AudioTrack>(
            value: realList[i],
            height: 38,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  _track.audio.id == realList[i].id
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: 16,
                  color: _track.audio.id == realList[i].id
                      ? const Color(0xFF38BDF8)
                      : Colors.grey,
                ),
                const SizedBox(width: 8),
                Text(
                  _formatAudioTrackTitle(realList[i], i),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: _track.audio.id == realList[i].id
                        ? FontWeight.w700
                        : FontWeight.normal,
                    color: _track.audio.id == realList[i].id
                        ? Colors.white
                        : const Color(0xFFCBD5E1),
                  ),
                ),
              ],
            ),
          ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: const Color(0xFF38BDF8).withValues(alpha: 0.5),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.audiotrack_rounded,
              size: 14,
              color: Color(0xFF38BDF8),
            ),
            const SizedBox(width: 6),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 160),
              child: Text(
                _currentAudioLabel,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF38BDF8),
                ),
              ),
            ),
            const SizedBox(width: 4),
            const Icon(
              Icons.arrow_drop_down_rounded,
              size: 16,
              color: Color(0xFF38BDF8),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubtitleTrackSelector() {
    if (!_canToggleSubtitles) return const SizedBox.shrink();

    final realSubs = _realSubtitleTracks;
    if (realSubs.length > 1) {
      return PopupMenuButton<SubtitleTrack>(
        tooltip: "Subtitr tilini tanlash / o'chirish",
        onSelected: (st) async {
          final player = _player;
          if (player == null) return;
          if (st.id == 'no') {
            setState(() => _subtitlesEnabled = false);
            await player.setSubtitleTrack(SubtitleTrack.no());
          } else {
            setState(() => _subtitlesEnabled = true);
            await player.setSubtitleTrack(st);
          }
        },
        color: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
          side: const BorderSide(color: Color(0xFF334155)),
        ),
        itemBuilder: (ctx) => [
          PopupMenuItem<SubtitleTrack>(
            value: SubtitleTrack.no(),
            height: 38,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  !_subtitlesEnabled || _track.subtitle.id == 'no'
                      ? Icons.check_circle_rounded
                      : Icons.radio_button_unchecked_rounded,
                  size: 16,
                  color: !_subtitlesEnabled || _track.subtitle.id == 'no'
                      ? Colors.amberAccent
                      : Colors.grey,
                ),
                const SizedBox(width: 8),
                const Text(
                  "Subtitrni o'chirish",
                  style: TextStyle(fontSize: 12, color: Color(0xFFCBD5E1)),
                ),
              ],
            ),
          ),
          for (int i = 0; i < realSubs.length; i++)
            PopupMenuItem<SubtitleTrack>(
              value: realSubs[i],
              height: 38,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                        ? Icons.check_circle_rounded
                        : Icons.radio_button_unchecked_rounded,
                    size: 16,
                    color: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                        ? Colors.amberAccent
                        : Colors.grey,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatSubtitleTrackTitle(realSubs[i], i),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                          ? FontWeight.w700
                          : FontWeight.normal,
                      color: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id
                          ? Colors.white
                          : const Color(0xFFCBD5E1),
                    ),
                  ),
                ],
              ),
            ),
        ],
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: _subtitlesEnabled
                ? Colors.amberAccent.withValues(alpha: 0.18)
                : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: _subtitlesEnabled
                  ? Colors.amberAccent.withValues(alpha: 0.5)
                  : Colors.white.withValues(alpha: 0.15),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _subtitlesEnabled
                    ? Icons.subtitles_rounded
                    : Icons.subtitles_off_rounded,
                size: 14,
                color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey,
              ),
              const SizedBox(width: 6),
              Text(
                _subtitlesEnabled ? "Subtitr: Yoqiq" : "Subtitr: O'chiq",
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey,
                ),
              ),
              const SizedBox(width: 4),
              Icon(
                Icons.arrow_drop_down_rounded,
                size: 16,
                color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey,
              ),
            ],
          ),
        ),
      );
    }

    return Tooltip(
      message: _subtitlesEnabled
          ? "Subtitrni o'chirish (ustidagi qatlamni yashirish)"
          : "Subtitrni yoqish",
      child: InkWell(
        onTap: _toggleSubtitles,
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(
            horizontal: 10,
            vertical: 5,
          ),
          decoration: BoxDecoration(
            color: _subtitlesEnabled
                ? Colors.amberAccent.withValues(alpha: 0.18)
                : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: _subtitlesEnabled
                  ? Colors.amberAccent.withValues(alpha: 0.5)
                  : Colors.white.withValues(alpha: 0.15),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _subtitlesEnabled
                    ? Icons.subtitles_rounded
                    : Icons.subtitles_off_rounded,
                size: 14,
                color: _subtitlesEnabled
                    ? Colors.amberAccent
                    : Colors.grey,
              ),
              const SizedBox(width: 6),
              Text(
                _subtitlesEnabled ? "Subtitr: Yoqiq" : "Subtitr: O'chiq",
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: _subtitlesEnabled
                      ? Colors.amberAccent
                      : Colors.grey,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _tracksSub?.cancel();
    _trackSub?.cancel();
    _player?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return CallbackShortcuts(
      bindings: {
        const SingleActivator(LogicalKeyboardKey.escape): widget.onClose,
      },
      child: Focus(
        autofocus: true,
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xFF0A0A0A),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF222222)),
          ),
          clipBehavior: Clip.antiAlias,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Yuqori sarlavha va boshqaruv paneli
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: const BoxDecoration(
                  color: Color(0xFF111111),
                  border: Border(
                    bottom: BorderSide(color: Color(0xFF222222)),
                  ),
                ),
                child: Row(
                  children: [
                    OutlinedButton.icon(
                      onPressed: widget.onClose,
                      icon: const Icon(Icons.arrow_back_rounded, size: 16),
                      label: const Text("Boshqaruv paneli"),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Container(height: 20, width: 1, color: const Color(0xFF333333)),
                    const SizedBox(width: 12),
                    const Icon(
                      Icons.movie_filter_rounded,
                      color: Colors.white,
                      size: 18,
                    ),
                    const SizedBox(width: 8),
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
                    _buildAudioTrackSelector(),
                    if (_realAudioTracks.length > 1) const SizedBox(width: 8),
                    _buildSubtitleTrackSelector(),
                    const SizedBox(width: 10),
                    if (widget.onOpenExternal != null)
                      IconButton(
                        tooltip: "Tashqi pleyerda ochish (VLC / mpv)",
                        onPressed: () {
                          _player?.pause();
                          widget.onOpenExternal!(widget.videoPath);
                        },
                        icon: const Icon(Icons.open_in_new_rounded, size: 18),
                        style: IconButton.styleFrom(
                          padding: const EdgeInsets.all(6),
                          minimumSize: const Size(32, 32),
                        ),
                      ),
                    IconButton(
                      tooltip: "Yopish (Esc)",
                      onPressed: widget.onClose,
                      icon: const Icon(Icons.close_rounded, size: 20),
                      style: IconButton.styleFrom(
                        padding: const EdgeInsets.all(6),
                        minimumSize: const Size(32, 32),
                      ),
                    ),
                  ],
                ),
              ),

              // Asosiy video maydoni
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
                  onPressed: () => widget.onOpenExternal!(widget.videoPath),
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
