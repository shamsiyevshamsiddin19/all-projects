import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

import 'subtitle_player.dart' show playerAvailable;

/// Aspect ratio variantlari
enum VideoAspectRatioMode {
  fitMode('Asl (Fit)', BoxFit.contain),
  fillMode("To'ldirish (Fill)", BoxFit.cover),
  widescreen('16:9', BoxFit.contain, 16 / 9),
  standard('4:3', BoxFit.contain, 4 / 3);

  const VideoAspectRatioMode(this.label, this.boxFit, [this.aspectRatio]);
  final String label;
  final BoxFit boxFit;
  final double? aspectRatio;
}

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
      barrierColor: Colors.black.withValues(alpha: 0.88),
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
  bool _isFullscreen = false;

  void _toggleFullscreen() {
    setState(() => _isFullscreen = !_isFullscreen);
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final dialogWidth = _isFullscreen ? size.width : (size.width * 0.90).clamp(640.0, 1340.0);
    final dialogHeight = _isFullscreen ? size.height : (size.height * 0.90).clamp(440.0, 880.0);

    return Dialog(
      backgroundColor: Colors.black,
      insetPadding: _isFullscreen ? EdgeInsets.zero : const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(_isFullscreen ? 0 : 16),
        side: BorderSide(color: _isFullscreen ? Colors.transparent : const Color(0xFF26262B)),
      ),
      clipBehavior: Clip.antiAlias,
      child: SizedBox(
        width: dialogWidth,
        height: dialogHeight,
        child: StudioVideoPlayer(
          videoPath: widget.videoPath,
          subtitlePath: widget.subtitlePath,
          title: widget.title,
          onClose: () => Navigator.of(context).pop(),
          onOpenExternal: widget.onOpenExternal != null ? (p) => widget.onOpenExternal!() : null,
          isFullscreen: _isFullscreen,
          onToggleFullscreen: _toggleFullscreen,
          headerLeading: const Icon(Icons.movie_filter_rounded, color: Color(0xFF38BDF8), size: 20),
        ),
      ),
    );
  }
}

/// Asosiy oynaning o'ng tomonida to'g'ridan-to'g'ri integratsiya qilingan
/// video pleyer paneli.
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
  bool _isFullscreen = false;

  void _toggleFullscreen() {
    setState(() => _isFullscreen = !_isFullscreen);
  }

  @override
  Widget build(BuildContext context) {
    if (_isFullscreen) {
      return Dialog.fullscreen(
        backgroundColor: Colors.black,
        child: StudioVideoPlayer(
          videoPath: widget.videoPath,
          subtitlePath: widget.subtitlePath,
          title: widget.title,
          onClose: _toggleFullscreen,
          onOpenExternal: widget.onOpenExternal,
          isFullscreen: true,
          onToggleFullscreen: _toggleFullscreen,
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0C),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF222226)),
      ),
      clipBehavior: Clip.antiAlias,
      child: StudioVideoPlayer(
        videoPath: widget.videoPath,
        subtitlePath: widget.subtitlePath,
        title: widget.title,
        onClose: widget.onClose,
        onOpenExternal: widget.onOpenExternal,
        isFullscreen: false,
        onToggleFullscreen: _toggleFullscreen,
        headerLeading: OutlinedButton.icon(
          onPressed: widget.onClose,
          icon: const Icon(Icons.arrow_back_rounded, size: 15),
          label: const Text("Boshqaruv paneli"),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            textStyle: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600),
            side: const BorderSide(color: Color(0xFF33333C)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        ),
      ),
    );
  }
}

/// Professional darajadagi kino va subtitr ko'rish pleyeri:
/// - Kadr-ma-kadr ko'rish (Frame stepping: `,` va `.`)
/// - Tezlikni boshqarish (0.5x - 2.0x va `[` / `]`)
/// - Jonli subtitr sinxronlash / kechiktirish (-500ms .. +500ms va `Z` / `X`)
/// - 150% ovoz kuchaytirgich (Volume boost)
/// - A-B takrorlash (A-B loop) va video sikli (`R`)
/// - Kadr suratini olish (Instant screenshot `P` / 📸)
/// - Kadr proporsiyasini o'zgartirish (Fit, Fill, 16:9, 4:3)
/// - Ko'p audio trek (Asl ovoz / AI Dublyaj `A`)
/// - To'liq klaviatura tezkor tugmalari va OSD xabarnomalari
class StudioVideoPlayer extends StatefulWidget {
  const StudioVideoPlayer({
    super.key,
    required this.videoPath,
    this.subtitlePath,
    this.title,
    required this.onClose,
    this.onOpenExternal,
    this.isFullscreen = false,
    this.onToggleFullscreen,
    this.headerLeading,
  });

  final String videoPath;
  final String? subtitlePath;
  final String? title;
  final VoidCallback onClose;
  final ValueChanged<String>? onOpenExternal;
  final bool isFullscreen;
  final VoidCallback? onToggleFullscreen;
  final Widget? headerLeading;

  @override
  State<StudioVideoPlayer> createState() => _StudioVideoPlayerState();
}

class _StudioVideoPlayerState extends State<StudioVideoPlayer> {
  Player? _player;
  VideoController? _video;
  bool _ready = false;
  String? _error;

  // Stream obunalari
  StreamSubscription<Tracks>? _tracksSub;
  StreamSubscription<Track>? _trackSub;
  StreamSubscription<Duration>? _posSub;
  StreamSubscription<Duration>? _durSub;
  StreamSubscription<bool>? _playingSub;
  StreamSubscription<double>? _volumeSub;
  StreamSubscription<double>? _rateSub;

  // Pleyer holati
  Tracks _tracks = const Tracks();
  Track _track = const Track();
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _playing = false;
  double _volume = 100.0;
  double _rate = 1.0;
  bool _isMuted = false;
  double _volumeBeforeMute = 100.0;

  // Subtitr va dublyaj sozlamalari
  bool _subtitlesEnabled = true;
  double _subtitleDelaySec = 0.0;

  // A-B takrorlash va sikl
  Duration? _loopA;
  Duration? _loopB;
  bool _isLoopingVideo = false;

  // Ko'rinish va interfeys
  VideoAspectRatioMode _aspectRatioMode = VideoAspectRatioMode.fitMode;
  bool _showRemainingTime = false;
  bool _controlsVisible = true;
  Timer? _controlsHideTimer;

  // On-Screen Display (OSD)
  String? _osdText;
  IconData? _osdIcon;
  Timer? _osdTimer;
  bool _showOsd = false;

  final FocusNode _focusNode = FocusNode();

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

  bool get _isImageFile {
    final lower = widget.videoPath.toLowerCase();
    return lower.endsWith('.jpg') ||
        lower.endsWith('.jpeg') ||
        lower.endsWith('.png') ||
        lower.endsWith('.webp') ||
        lower.endsWith('.gif');
  }

  bool get _isBurnedVideo {
    final lower = widget.videoPath.toLowerCase();
    return lower.contains('_dual.') ||
        lower.contains('_single.') ||
        lower.contains('_dual_vocab.') ||
        lower.contains('_original_vocab.') ||
        lower.contains('_original.') ||
        lower.contains('_translated.');
  }

  List<AudioTrack> get _realAudioTracks {
    return _tracks.audio.where((t) => t.id != 'auto' && t.id != 'no').toList();
  }

  List<SubtitleTrack> get _realSubtitleTracks {
    return _tracks.subtitle.where((t) => t.id != 'auto' && t.id != 'no').toList();
  }

  bool get _canToggleSubtitles =>
      !_isBurnedVideo && (_hasSubtitles || _realSubtitleTracks.isNotEmpty);

  @override
  void initState() {
    super.initState();
    _subtitlesEnabled = !_isBurnedVideo;
    _initPlayer();
  }

  @override
  void didUpdateWidget(StudioVideoPlayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.videoPath != oldWidget.videoPath ||
        widget.subtitlePath != oldWidget.subtitlePath) {
      _subtitlesEnabled = !_isBurnedVideo;
      _loopA = null;
      _loopB = null;
      _subtitleDelaySec = 0.0;
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
      _posSub = player.stream.position.listen((pos) {
        if (!mounted) return;
        setState(() => _position = pos);

        // A-B Loop tekshiruvi
        if (_loopA != null && _loopB != null) {
          if (pos >= _loopB! || pos < _loopA!) {
            player.seek(_loopA!);
          }
        }
      });
      _durSub = player.stream.duration.listen((dur) {
        if (mounted) setState(() => _duration = dur);
      });
      _playingSub = player.stream.playing.listen((p) {
        if (mounted) {
          setState(() => _playing = p);
          if (p) {
            _startControlsHideTimer();
          } else {
            _showControlsPermanently();
          }
        }
      });
      _volumeSub = player.stream.volume.listen((v) {
        if (mounted) setState(() => _volume = v);
      });
      _rateSub = player.stream.rate.listen((r) {
        if (mounted) setState(() => _rate = r);
      });

      // 150% ovoz kuchaytirgich limitini ochish
      try {
        if (player.platform is NativePlayer) {
          final np = player.platform as NativePlayer;
          await np.setProperty('volume-max', '150.0');
        }
      } catch (_) {}

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
        setState(() => _error = e.toString());
      }
    }
  }

  Future<void> _loadMedia() async {
    if (_isImageFile) {
      if (mounted) {
        setState(() {
          _ready = true;
          _error = null;
        });
        _focusNode.requestFocus();
      }
      return;
    }

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
        _focusNode.requestFocus();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = e.toString());
      }
    }
  }

  @override
  void dispose() {
    _controlsHideTimer?.cancel();
    _osdTimer?.cancel();
    _tracksSub?.cancel();
    _trackSub?.cancel();
    _posSub?.cancel();
    _durSub?.cancel();
    _playingSub?.cancel();
    _volumeSub?.cancel();
    _rateSub?.cancel();
    _focusNode.dispose();
    _player?.dispose();
    super.dispose();
  }

  // --- OSD (On-Screen Display) xabarnomalari ---
  void _showOSD(String text, IconData icon) {
    _osdTimer?.cancel();
    if (mounted) {
      setState(() {
        _osdText = text;
        _osdIcon = icon;
        _showOsd = true;
      });
      _osdTimer = Timer(const Duration(milliseconds: 1400), () {
        if (mounted) setState(() => _showOsd = false);
      });
    }
  }

  // --- Boshqaruv panelini avto-yashirish ---
  void _startControlsHideTimer() {
    _controlsHideTimer?.cancel();
    if (_playing) {
      _controlsHideTimer = Timer(const Duration(milliseconds: 3200), () {
        if (mounted && _playing) {
          setState(() => _controlsVisible = false);
        }
      });
    }
  }

  void _onUserInteraction() {
    if (!_controlsVisible) {
      setState(() => _controlsVisible = true);
    }
    _startControlsHideTimer();
  }

  void _showControlsPermanently() {
    _controlsHideTimer?.cancel();
    setState(() => _controlsVisible = true);
  }

  // --- Pleyer amallari ---
  Future<void> _playOrPause() async {
    final player = _player;
    if (player == null) return;
    await player.playOrPause();
    _showOSD(_playing ? "Pauza" : "O'ynatish", _playing ? Icons.pause_rounded : Icons.play_arrow_rounded);
  }

  Future<void> _seekRelative(Duration delta) async {
    final player = _player;
    if (player == null) return;
    final target = _position + delta;
    final clamped = target < Duration.zero
        ? Duration.zero
        : (target > _duration && _duration > Duration.zero ? _duration : target);
    await player.seek(clamped);
    final sign = delta.isNegative ? '' : '+';
    final sec = delta.inSeconds != 0 ? '${delta.inSeconds}s' : '${delta.inMilliseconds}ms';
    _showOSD(
      "$sign$sec (${_formatDuration(clamped)})",
      delta.isNegative ? Icons.replay_5_rounded : Icons.forward_5_rounded,
    );
  }

  Duration _clampDuration(Duration val, Duration min, Duration max) {
    if (val < min) return min;
    if (val > max) return max;
    return val;
  }

  Future<void> _stepFrame({required bool forward}) async {
    final player = _player;
    if (player == null) return;
    if (_playing) await player.pause();

    try {
      if (player.platform is NativePlayer) {
        final np = player.platform as NativePlayer;
        await np.command([forward ? 'frame-step' : 'frame-back-step']);
      } else {
        final delta = Duration(milliseconds: forward ? 42 : -42);
        await player.seek(_clampDuration(_position + delta, Duration.zero, _duration));
      }
    } catch (_) {
      final delta = Duration(milliseconds: forward ? 42 : -42);
      await player.seek(_clampDuration(_position + delta, Duration.zero, _duration));
    }
    _showOSD(forward ? "+1 kadr (oldinga)" : "-1 kadr (orqaga)", forward ? Icons.last_page_rounded : Icons.first_page_rounded);
  }

  Future<void> _setVolume(double newVol) async {
    final player = _player;
    if (player == null) return;
    final clamped = newVol.clamp(0.0, 150.0);
    setState(() {
      _volume = clamped;
      _isMuted = clamped == 0;
    });
    await player.setVolume(clamped);
    _showOSD(
      clamped > 100.0 ? "Ovoz: ${clamped.round()}% (Kuchaytirilgan 🔥)" : "Ovoz: ${clamped.round()}%",
      clamped == 0 ? Icons.volume_off_rounded : (clamped > 100 ? Icons.volume_up_rounded : Icons.volume_down_rounded),
    );
  }

  Future<void> _toggleMute() async {
    final player = _player;
    if (player == null) return;
    if (_isMuted || _volume == 0) {
      final restore = _volumeBeforeMute > 0 ? _volumeBeforeMute : 100.0;
      await _setVolume(restore);
      _showOSD("Ovoz: ${restore.round()}%", Icons.volume_up_rounded);
    } else {
      _volumeBeforeMute = _volume;
      await _setVolume(0.0);
      _showOSD("Ovozsiz (Muted)", Icons.volume_off_rounded);
    }
  }

  Future<void> _setRate(double rate) async {
    final player = _player;
    if (player == null) return;
    setState(() => _rate = rate);
    await player.setRate(rate);
    _showOSD("Tezlik: ${rate.toStringAsFixed(2)}x", Icons.speed_rounded);
  }

  void _cycleRate({required bool faster}) {
    const rates = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0];
    int idx = rates.indexWhere((r) => (r - _rate).abs() < 0.05);
    if (idx == -1) idx = 2; // 1.0
    final nextIdx = faster ? (idx + 1).clamp(0, rates.length - 1) : (idx - 1).clamp(0, rates.length - 1);
    _setRate(rates[nextIdx]);
  }

  Future<void> _setSubtitleDelay(double delaySec) async {
    final player = _player;
    if (player == null) return;
    setState(() => _subtitleDelaySec = delaySec);
    try {
      if (player.platform is NativePlayer) {
        final np = player.platform as NativePlayer;
        await np.setProperty('sub-delay', delaySec.toStringAsFixed(2));
      }
    } catch (_) {}
    final sign = delaySec >= 0 ? '+' : '';
    _showOSD("Subtitr sinxroni: $sign${delaySec.toStringAsFixed(2)}s", Icons.sync_rounded);
  }

  Future<void> _toggleSubtitles() async {
    final player = _player;
    if (player == null || !_canToggleSubtitles) return;
    final next = !_subtitlesEnabled;
    setState(() => _subtitlesEnabled = next);
    try {
      if (next) {
        if (_hasSubtitles) {
          await player.setSubtitleTrack(SubtitleTrack.uri(Uri.file(widget.subtitlePath!).toString()));
        } else if (_realSubtitleTracks.isNotEmpty) {
          await player.setSubtitleTrack(_realSubtitleTracks.first);
        }
      } else {
        await player.setSubtitleTrack(SubtitleTrack.no());
      }
    } catch (_) {}
    _showOSD(next ? "Subtitr: Yoqildi" : "Subtitr: O'chirildi", next ? Icons.subtitles_rounded : Icons.subtitles_off_rounded);
  }

  void _cycleAudioTrack() {
    final realList = _realAudioTracks;
    if (realList.length <= 1) return;
    final cur = _track.audio;
    final curIdx = realList.indexWhere((t) => t.id == cur.id);
    final nextIdx = (curIdx + 1) % realList.length;
    final nextTrack = realList[nextIdx];
    _player?.setAudioTrack(nextTrack);
    _showOSD("Audio: ${_formatAudioTrackTitle(nextTrack, nextIdx)}", Icons.audiotrack_rounded);
  }

  void _toggleABLoop() {
    if (_loopA == null) {
      setState(() => _loopA = _position);
      _showOSD("[A] nuqta belgilandi: ${_formatDuration(_position)}", Icons.repeat_one_rounded);
    } else if (_loopB == null) {
      if (_position > _loopA!) {
        setState(() => _loopB = _position);
      } else {
        setState(() {
          _loopB = _loopA;
          _loopA = _position;
        });
      }
      _showOSD("A-B Takrorlash faol: ${_formatDuration(_loopA!)} ➔ ${_formatDuration(_loopB!)}", Icons.repeat_rounded);
    } else {
      setState(() {
        _loopA = null;
        _loopB = null;
      });
      _showOSD("A-B Takrorlash bekor qilindi", Icons.close_rounded);
    }
  }

  Future<void> _toggleVideoLoop() async {
    final player = _player;
    if (player == null) return;
    final next = !_isLoopingVideo;
    setState(() => _isLoopingVideo = next);
    await player.setPlaylistMode(next ? PlaylistMode.single : PlaylistMode.none);
    _showOSD(next ? "Video cheksiz takrorlashda" : "Takrorlash o'chirildi", Icons.loop_rounded);
  }

  Future<void> _takeSnapshot() async {
    final player = _player;
    if (player == null) return;
    try {
      final Uint8List? bytes = await player.screenshot(includeLibassSubtitles: true);
      if (bytes != null && bytes.isNotEmpty) {
        final videoFile = File(widget.videoPath);
        final dir = videoFile.parent;
        final base = videoFile.uri.pathSegments.last.replaceAll(RegExp(r'\.[a-zA-Z0-9]+$'), '');
        final stamp = DateTime.now().millisecondsSinceEpoch;
        final outName = '${base}_kadr_$stamp.jpg';
        final outFile = File('${dir.path}/$outName');
        await outFile.writeAsBytes(bytes);
        _showOSD("📸 Kadr saqlandi: $outName", Icons.camera_alt_rounded);
      } else {
        _showOSD("Kadrni saqlab bo'lmadi", Icons.warning_amber_rounded);
      }
    } catch (e) {
      _showOSD("Kadr xatosi: $e", Icons.error_outline_rounded);
    }
  }

  void _cycleAspectRatio() {
    const modes = VideoAspectRatioMode.values;
    final nextIdx = (_aspectRatioMode.index + 1) % modes.length;
    setState(() => _aspectRatioMode = modes[nextIdx]);
    _showOSD("Kadr: ${_aspectRatioMode.label}", Icons.aspect_ratio_rounded);
  }

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

  String _formatDuration(Duration d) {
    final h = d.inHours;
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    if (h > 0) return '$h:$m:$s';
    return '$m:$s';
  }

  void _showShortcutsHelp() {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF141416),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFF2A2A32)),
        ),
        title: const Row(
          children: [
            Icon(Icons.keyboard_rounded, color: Color(0xFF38BDF8), size: 22),
            SizedBox(width: 10),
            Text(
              "Klaviatura tezkor tugmalari",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
            ),
          ],
        ),
        content: SizedBox(
          width: 520,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                _shortcutRow("Bo'sh joy / K", "O'ynatish / To'xtatish (Play / Pause)"),
                _shortcutRow("← / →", "5 soniya orqaga / oldinga sakrash"),
                _shortcutRow("Shift + ← / →", "1 soniya aniq orqaga / oldinga"),
                _shortcutRow("J / L", "10 soniya orqaga / oldinga sakrash"),
                _shortcutRow(", / .", "1 kadr orqaga / 1 kadr oldinga (Frame step)"),
                _shortcutRow("↑ / ↓", "Ovozni 5% ga ko'tarish / pasaytirish"),
                _shortcutRow("M", "Ovozni o'chirish / yoqish (Mute)"),
                _shortcutRow("[ / ]", "Tezlikni kamaytirish / oshirish (0.5x - 2.0x)"),
                _shortcutRow("Backspace", "Tezlikni 1.0x (normal) ga qaytarish"),
                _shortcutRow("A", "Audio trekni almashtirish (Asl ovoz ↔ Dublyaj)"),
                _shortcutRow("C / S", "Subtitrni yoqish / o'chirish"),
                _shortcutRow("Z / X", "Subtitr sinxroni (-100ms / +100ms)"),
                _shortcutRow("R", "A-B takrorlash nuqtalarini belgilash"),
                _shortcutRow("P", "Joriy kadr suratini saqlash (Snapshot)"),
                _shortcutRow("F / 2x Bosish", "To'liq ekran rejimiga o'tish (Fullscreen)"),
                _shortcutRow("0 .. 9", "Video davomiyligining 0% .. 90% qismiga sakrash"),
                _shortcutRow("? / H", "Ushbu yordam oynasini ochish"),
                _shortcutRow("Esc", "To'liq ekrandan chiqish / Pleyerni yopish"),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text("Tushunarli", style: TextStyle(color: Color(0xFF38BDF8))),
          ),
        ],
      ),
    );
  }

  Widget _shortcutRow(String keyCombination, String action) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.5),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: const Color(0xFF1E222B),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: const Color(0xFF333B4D)),
            ),
            child: Text(
              keyCombination,
              style: const TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
                color: Color(0xFF38BDF8),
                fontFamily: 'monospace',
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              action,
              style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1)),
            ),
          ),
        ],
      ),
    );
  }

  // --- Klaviatura hodisalari ---
  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is! KeyDownEvent) return KeyEventResult.ignored;

    final key = event.logicalKey;
    final isShift = HardwareKeyboard.instance.isShiftPressed;

    if (key == LogicalKeyboardKey.space || key == LogicalKeyboardKey.keyK) {
      _playOrPause();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.arrowLeft) {
      _seekRelative(Duration(seconds: isShift ? -1 : -5));
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.arrowRight) {
      _seekRelative(Duration(seconds: isShift ? 1 : 5));
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyJ) {
      _seekRelative(const Duration(seconds: -10));
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyL) {
      _seekRelative(const Duration(seconds: 10));
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.comma) {
      _stepFrame(forward: false);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.period) {
      _stepFrame(forward: true);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.arrowUp) {
      _setVolume(_volume + 5.0);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.arrowDown) {
      _setVolume(_volume - 5.0);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyM) {
      _toggleMute();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.bracketLeft) {
      _cycleRate(faster: false);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.bracketRight) {
      _cycleRate(faster: true);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.backspace) {
      _setRate(1.0);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyA) {
      _cycleAudioTrack();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyC || key == LogicalKeyboardKey.keyS) {
      _toggleSubtitles();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyZ) {
      _setSubtitleDelay(_subtitleDelaySec - 0.1);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyX) {
      _setSubtitleDelay(_subtitleDelaySec + 0.1);
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyR) {
      _toggleABLoop();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyP) {
      _takeSnapshot();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.keyF) {
      if (widget.onToggleFullscreen != null) widget.onToggleFullscreen!();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.slash || key == LogicalKeyboardKey.keyH) {
      _showShortcutsHelp();
      return KeyEventResult.handled;
    }
    if (key == LogicalKeyboardKey.escape) {
      if (widget.isFullscreen && widget.onToggleFullscreen != null) {
        widget.onToggleFullscreen!();
      } else {
        widget.onClose();
      }
      return KeyEventResult.handled;
    }

    // 0..9 foizga sakrash
    if (key.keyId >= LogicalKeyboardKey.digit0.keyId && key.keyId <= LogicalKeyboardKey.digit9.keyId) {
      final num = key.keyId - LogicalKeyboardKey.digit0.keyId;
      if (_duration > Duration.zero) {
        final targetMs = (_duration.inMilliseconds * (num / 10.0)).round();
        _player?.seek(Duration(milliseconds: targetMs));
        _showOSD("Sakrash: ${num * 10}% (${_formatDuration(Duration(milliseconds: targetMs))})", Icons.fast_forward_rounded);
      }
      return KeyEventResult.handled;
    }

    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    return Focus(
      focusNode: _focusNode,
      autofocus: true,
      onKeyEvent: _handleKeyEvent,
      child: MouseRegion(
        onHover: (_) => _onUserInteraction(),
        child: Container(
          color: Colors.black,
          child: Stack(
            children: [
              // 1. Asosiy video qatlami va Imo-ishoralar
              Positioned.fill(
                child: GestureDetector(
                  onTap: () {
                    _playOrPause();
                    _onUserInteraction();
                  },
                  onDoubleTap: () {
                    if (widget.onToggleFullscreen != null) {
                      widget.onToggleFullscreen!();
                    }
                  },
                  child: Center(
                    child: _buildVideoSurface(),
                  ),
                ),
              ),

              // 2. Markaziy OSD HUD bildirishnomasi
              Center(
                child: AnimatedOpacity(
                  opacity: _showOsd ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 200),
                  child: IgnorePointer(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 11),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.82),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.5)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.6),
                            blurRadius: 16,
                            spreadRadius: 2,
                          ),
                        ],
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (_osdIcon != null) ...[
                            Icon(_osdIcon, color: const Color(0xFF38BDF8), size: 22),
                            const SizedBox(width: 10),
                          ],
                          Text(
                            _osdText ?? '',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 13.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),

              // 3. Yuqori sarlavha va boshqaruv paneli (Auto-hide)
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                child: AnimatedOpacity(
                  opacity: _controlsVisible ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 250),
                  child: IgnorePointer(
                    ignoring: !_controlsVisible,
                    child: _buildTopHeader(),
                  ),
                ),
              ),

              // 4. Pastki Studio boshqaruv doki (Auto-hide)
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: AnimatedOpacity(
                  opacity: _controlsVisible ? 1.0 : 0.0,
                  duration: const Duration(milliseconds: 250),
                  child: IgnorePointer(
                    ignoring: !_controlsVisible,
                    child: _buildBottomStudioDock(),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildVideoSurface() {
    if (_isImageFile) {
      return Center(
        child: Image.file(
          File(widget.videoPath),
          fit: _aspectRatioMode.boxFit,
          errorBuilder: (context, error, stackTrace) => const Center(
            child: Text("Rasmni ochib bo'lmadi", style: TextStyle(color: Colors.white70)),
          ),
        ),
      );
    }

    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline_rounded, color: Colors.redAccent, size: 48),
            const SizedBox(height: 14),
            const Text(
              "Videoni o'rnatilgan pleyerda ochib bo'lmadi",
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white),
            ),
            const SizedBox(height: 8),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey, fontSize: 12),
            ),
            const SizedBox(height: 18),
            if (widget.onOpenExternal != null)
              FilledButton.icon(
                onPressed: () => widget.onOpenExternal!(widget.videoPath),
                icon: const Icon(Icons.open_in_new_rounded, size: 16),
                label: const Text("Tashqi ilovada ochish"),
              ),
          ],
        ),
      );
    }

    if (!_ready || _video == null) {
      return const SizedBox(
        width: 32,
        height: 32,
        child: CircularProgressIndicator(strokeWidth: 2.5, color: Color(0xFF38BDF8)),
      );
    }

    final mode = _aspectRatioMode;
    if (mode.aspectRatio != null) {
      return AspectRatio(
        aspectRatio: mode.aspectRatio!,
        child: Video(
          controller: _video!,
          controls: NoVideoControls,
          fit: mode.boxFit,
        ),
      );
    }

    return Video(
      controller: _video!,
      controls: NoVideoControls,
      fit: mode.boxFit,
    );
  }

  // --- Yuqori panel ---
  Widget _buildTopHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.black.withValues(alpha: 0.90),
            Colors.black.withValues(alpha: 0.65),
            Colors.transparent,
          ],
        ),
      ),
      child: Row(
        children: [
          if (widget.headerLeading != null) ...[
            widget.headerLeading!,
            const SizedBox(width: 10),
          ],
          Expanded(
            child: Text(
              _displayName,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 13.5,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(width: 8),

          // Subtitr sinxron nishoni (agar kechikish bo'lsa)
          if (_subtitleDelaySec != 0.0) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF38BDF8).withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.5)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.sync_rounded, size: 13, color: Color(0xFF38BDF8)),
                  const SizedBox(width: 4),
                  Text(
                    "Sinxron: ${_subtitleDelaySec >= 0 ? '+' : ''}${_subtitleDelaySec.toStringAsFixed(1)}s",
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF38BDF8)),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
          ],

          // Audio trek tanlash
          _buildAudioTrackSelector(),
          if (_realAudioTracks.length > 1) const SizedBox(width: 8),

          // Subtitr tanlash
          _buildSubtitleTrackSelector(),
          const SizedBox(width: 8),

          // Kadr suratini olish (Snapshot)
          IconButton(
            tooltip: "Kadr suratini olish (P)",
            onPressed: _takeSnapshot,
            icon: const Icon(Icons.camera_alt_outlined, size: 18, color: Color(0xFFE2E8F0)),
            visualDensity: VisualDensity.compact,
          ),

          // Klaviatura yordam oynasi
          IconButton(
            tooltip: "Klaviatura tugmalari (?)",
            onPressed: _showShortcutsHelp,
            icon: const Icon(Icons.keyboard_outlined, size: 18, color: Color(0xFFE2E8F0)),
            visualDensity: VisualDensity.compact,
          ),

          // Tashqi pleyer
          if (widget.onOpenExternal != null)
            IconButton(
              tooltip: "Tashqi pleyerda ochish (VLC / mpv)",
              onPressed: () {
                _player?.pause();
                widget.onOpenExternal!(widget.videoPath);
              },
              icon: const Icon(Icons.open_in_new_rounded, size: 18, color: Color(0xFFE2E8F0)),
              visualDensity: VisualDensity.compact,
            ),

          // To'liq ekran tugmasi
          if (widget.onToggleFullscreen != null)
            IconButton(
              tooltip: widget.isFullscreen ? "To'liq ekrandan chiqish (F)" : "To'liq ekran (F)",
              onPressed: widget.onToggleFullscreen,
              icon: Icon(
                widget.isFullscreen ? Icons.fullscreen_exit_rounded : Icons.fullscreen_rounded,
                size: 20,
                color: Color(0xFFE2E8F0),
              ),
              visualDensity: VisualDensity.compact,
            ),

          // Yopish tugmasi
          IconButton(
            tooltip: "Yopish (Esc)",
            onPressed: widget.onClose,
            icon: const Icon(Icons.close_rounded, size: 20, color: Color(0xFFE2E8F0)),
            visualDensity: VisualDensity.compact,
          ),
        ],
      ),
    );
  }

  // --- Audio trek tanlagich ---
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
                  color: _track.audio.id == realList[i].id ? const Color(0xFF38BDF8) : Colors.grey,
                ),
                const SizedBox(width: 8),
                Text(
                  _formatAudioTrackTitle(realList[i], i),
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: _track.audio.id == realList[i].id ? FontWeight.w700 : FontWeight.normal,
                    color: _track.audio.id == realList[i].id ? Colors.white : const Color(0xFFCBD5E1),
                  ),
                ),
              ],
            ),
          ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
        decoration: BoxDecoration(
          color: const Color(0xFF0F172A),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: const Color(0xFF38BDF8).withValues(alpha: 0.5)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.audiotrack_rounded, size: 14, color: Color(0xFF38BDF8)),
            const SizedBox(width: 6),
            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 150),
              child: Text(
                _currentAudioLabel,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF38BDF8)),
              ),
            ),
            const SizedBox(width: 4),
            const Icon(Icons.arrow_drop_down_rounded, size: 16, color: Color(0xFF38BDF8)),
          ],
        ),
      ),
    );
  }

  // --- Subtitr trek tanlagich ---
  Widget _buildSubtitleTrackSelector() {
    if (!_canToggleSubtitles) return const SizedBox.shrink();

    final realSubs = _realSubtitleTracks;
    if (realSubs.length > 1) {
      return PopupMenuButton<SubtitleTrack>(
        tooltip: "Subtitr tilini tanlash / o'chirish (C)",
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
                  color: !_subtitlesEnabled || _track.subtitle.id == 'no' ? Colors.amberAccent : Colors.grey,
                ),
                const SizedBox(width: 8),
                const Text("Subtitrni o'chirish", style: TextStyle(fontSize: 12, color: Color(0xFFCBD5E1))),
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
                    color: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id ? Colors.amberAccent : Colors.grey,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _formatSubtitleTrackTitle(realSubs[i], i),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id ? FontWeight.w700 : FontWeight.normal,
                      color: _subtitlesEnabled && _track.subtitle.id == realSubs[i].id ? Colors.white : const Color(0xFFCBD5E1),
                    ),
                  ),
                ],
              ),
            ),
        ],
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
          decoration: BoxDecoration(
            color: _subtitlesEnabled ? Colors.amberAccent.withValues(alpha: 0.18) : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: _subtitlesEnabled ? Colors.amberAccent.withValues(alpha: 0.5) : Colors.white.withValues(alpha: 0.15)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _subtitlesEnabled ? Icons.subtitles_rounded : Icons.subtitles_off_rounded,
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
              Icon(Icons.arrow_drop_down_rounded, size: 16, color: _subtitlesEnabled ? Colors.amberAccent : Colors.grey),
            ],
          ),
        ),
      );
    }

    return Tooltip(
      message: _subtitlesEnabled ? "Subtitrni o'chirish (C)" : "Subtitrni yoqish (C)",
      child: InkWell(
        onTap: _toggleSubtitles,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
          decoration: BoxDecoration(
            color: _subtitlesEnabled ? Colors.amberAccent.withValues(alpha: 0.18) : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: _subtitlesEnabled ? Colors.amberAccent.withValues(alpha: 0.5) : Colors.white.withValues(alpha: 0.15)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _subtitlesEnabled ? Icons.subtitles_rounded : Icons.subtitles_off_rounded,
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
            ],
          ),
        ),
      ),
    );
  }

  // --- Pastki Studio boshqaruv doki ---
  Widget _buildBottomStudioDock() {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 6, 14, 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [
            Colors.black.withValues(alpha: 0.95),
            Colors.black.withValues(alpha: 0.75),
            Colors.transparent,
          ],
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // 1. Interaktiv progress bar va vaqt indikatori
          _buildProgressBar(),

          const SizedBox(height: 4),

          // 2. Asosiy boshqaruv tugmalari paneli
          Row(
            children: [
              // Play / Pause
              IconButton(
                tooltip: _playing ? "To'xtatish (Space)" : "O'ynatish (Space)",
                onPressed: _playOrPause,
                icon: Icon(
                  _playing ? Icons.pause_rounded : Icons.play_arrow_rounded,
                  size: 26,
                  color: const Color(0xFF38BDF8),
                ),
                style: IconButton.styleFrom(
                  backgroundColor: const Color(0xFF1E293B),
                  padding: const EdgeInsets.all(6),
                ),
              ),
              const SizedBox(width: 6),

              // -10s orqaga
              IconButton(
                tooltip: "10 soniya orqaga (J)",
                onPressed: () => _seekRelative(const Duration(seconds: -10)),
                icon: const Icon(Icons.replay_10_rounded, size: 20, color: Color(0xFFCBD5E1)),
                visualDensity: VisualDensity.compact,
              ),

              // +10s oldinga
              IconButton(
                tooltip: "10 soniya oldinga (L)",
                onPressed: () => _seekRelative(const Duration(seconds: 10)),
                icon: const Icon(Icons.forward_10_rounded, size: 20, color: Color(0xFFCBD5E1)),
                visualDensity: VisualDensity.compact,
              ),

              // 1 kadr orqaga (frame step backward)
              IconButton(
                tooltip: "1 kadr orqaga (,)",
                onPressed: () => _stepFrame(forward: false),
                icon: const Icon(Icons.first_page_rounded, size: 19, color: Color(0xFF94A3B8)),
                visualDensity: VisualDensity.compact,
              ),

              // 1 kadr oldinga (frame step forward)
              IconButton(
                tooltip: "1 kadr oldinga (.)",
                onPressed: () => _stepFrame(forward: true),
                icon: const Icon(Icons.last_page_rounded, size: 19, color: Color(0xFF94A3B8)),
                visualDensity: VisualDensity.compact,
              ),

              const SizedBox(width: 8),

              // Ovoz boshqaruvi va 150% boost
              _buildVolumeControl(),

              const SizedBox(width: 12),

              // Vaqt matni
              InkWell(
                onTap: () => setState(() => _showRemainingTime = !_showRemainingTime),
                borderRadius: BorderRadius.circular(4),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  child: Text(
                    _showRemainingTime
                        ? "${_formatDuration(_position)} / -${_formatDuration(_duration > _position ? _duration - _position : Duration.zero)}"
                        : "${_formatDuration(_position)} / ${_formatDuration(_duration)}",
                    style: const TextStyle(
                      fontSize: 11.5,
                      color: Color(0xFFCBD5E1),
                      fontFamily: 'monospace',
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ),

              const Spacer(),

              // Subtitr sinxronlash popupi
              _buildSubtitleSyncButton(),
              const SizedBox(width: 6),

              // Tezlik menyusi
              _buildSpeedSelector(),
              const SizedBox(width: 6),

              // A-B Takrorlash
              _buildABLoopButton(),
              const SizedBox(width: 4),

              // Video sikli (Loop video)
              IconButton(
                tooltip: _isLoopingVideo ? "Videoni siklda o'ynash yoqilgan" : "Videoni siklda o'ynash (Loop)",
                onPressed: _toggleVideoLoop,
                icon: Icon(
                  Icons.loop_rounded,
                  size: 19,
                  color: _isLoopingVideo ? const Color(0xFF38BDF8) : const Color(0xFF64748B),
                ),
                visualDensity: VisualDensity.compact,
              ),

              // Kadr proporsiyasi (Aspect ratio)
              IconButton(
                tooltip: "Kadr proporsiyasi: ${_aspectRatioMode.label}",
                onPressed: _cycleAspectRatio,
                icon: const Icon(Icons.aspect_ratio_rounded, size: 19, color: Color(0xFFCBD5E1)),
                visualDensity: VisualDensity.compact,
              ),

              // To'liq ekran
              if (widget.onToggleFullscreen != null)
                IconButton(
                  tooltip: widget.isFullscreen ? "Kichik ekranga qaytish (F)" : "To'liq ekran (F)",
                  onPressed: widget.onToggleFullscreen,
                  icon: Icon(
                    widget.isFullscreen ? Icons.fullscreen_exit_rounded : Icons.fullscreen_rounded,
                    size: 21,
                    color: const Color(0xFFCBD5E1),
                  ),
                  visualDensity: VisualDensity.compact,
                ),
            ],
          ),
        ],
      ),
    );
  }

  // --- Silliq va A-B takrorlash belgili progress bar ---
  Widget _buildProgressBar() {
    final totalMs = _duration.inMilliseconds;
    final posMs = _position.inMilliseconds.clamp(0, totalMs > 0 ? totalMs : 0);
    final value = totalMs > 0 ? (posMs / totalMs).clamp(0.0, 1.0) : 0.0;

    return SliderTheme(
      data: SliderThemeData(
        trackHeight: 3.5,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
        overlayShape: const RoundSliderOverlayShape(overlayRadius: 12),
        activeTrackColor: const Color(0xFF38BDF8),
        inactiveTrackColor: const Color(0xFF26262B),
        thumbColor: Colors.white,
        overlayColor: const Color(0xFF38BDF8).withValues(alpha: 0.25),
      ),
      child: Slider(
        value: value,
        onChanged: (v) {
          if (totalMs > 0) {
            final targetMs = (v * totalMs).round();
            _player?.seek(Duration(milliseconds: targetMs));
          }
        },
      ),
    );
  }

  // --- Ovoz va 150% Super Boost ---
  Widget _buildVolumeControl() {
    final isBoosted = _volume > 100.0;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          tooltip: _isMuted ? "Ovozni yoqish (M)" : "Ovozsiz qilish (M)",
          onPressed: _toggleMute,
          icon: Icon(
            _isMuted || _volume == 0
                ? Icons.volume_off_rounded
                : (isBoosted ? Icons.volume_up_rounded : (_volume > 50 ? Icons.volume_up_rounded : Icons.volume_down_rounded)),
            size: 19,
            color: _isMuted || _volume == 0
                ? Colors.redAccent
                : (isBoosted ? Colors.amberAccent : const Color(0xFFCBD5E1)),
          ),
          visualDensity: VisualDensity.compact,
        ),
        SizedBox(
          width: 78,
          child: SliderTheme(
            data: SliderThemeData(
              trackHeight: 3.0,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 4.5),
              overlayShape: const RoundSliderOverlayShape(overlayRadius: 9),
              activeTrackColor: isBoosted ? Colors.amberAccent : const Color(0xFF38BDF8),
              inactiveTrackColor: const Color(0xFF26262B),
              thumbColor: isBoosted ? Colors.amberAccent : Colors.white,
            ),
            child: Slider(
              value: _volume.clamp(0.0, 150.0),
              min: 0.0,
              max: 150.0,
              onChanged: _setVolume,
            ),
          ),
        ),
        Text(
          "${_volume.round()}%",
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w600,
            color: isBoosted ? Colors.amberAccent : const Color(0xFF94A3B8),
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }

  // --- Subtitr sinxronlash popup tugmasi ---
  Widget _buildSubtitleSyncButton() {
    return PopupMenuButton<double>(
      tooltip: "Subtitr vaqtini to'g'irlash (Z / X)",
      onSelected: _setSubtitleDelay,
      color: const Color(0xFF1E293B),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: Color(0xFF334155)),
      ),
      itemBuilder: (ctx) => [
        const PopupMenuItem<double>(
          enabled: false,
          child: Text("Subtitr vaqtini siljitish:", style: TextStyle(fontSize: 11, color: Colors.grey)),
        ),
        const PopupMenuItem<double>(value: -0.5, child: Text("-0.50s (Ertaroq)")),
        const PopupMenuItem<double>(value: -0.2, child: Text("-0.20s")),
        const PopupMenuItem<double>(value: -0.1, child: Text("-0.10s (Z)")),
        const PopupMenuItem<double>(value: 0.0, child: Text("0.00s (Asl holat)", style: TextStyle(fontWeight: FontWeight.bold))),
        const PopupMenuItem<double>(value: 0.1, child: Text("+0.10s (X)")),
        const PopupMenuItem<double>(value: 0.2, child: Text("+0.20s")),
        const PopupMenuItem<double>(value: 0.5, child: Text("+0.50s (Kechroq)")),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
        decoration: BoxDecoration(
          color: _subtitleDelaySec != 0.0
              ? const Color(0xFF38BDF8).withValues(alpha: 0.2)
              : Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: _subtitleDelaySec != 0.0
                ? const Color(0xFF38BDF8).withValues(alpha: 0.5)
                : Colors.white.withValues(alpha: 0.12),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.sync_rounded, size: 13, color: Color(0xFFCBD5E1)),
            const SizedBox(width: 4),
            Text(
              "${_subtitleDelaySec >= 0 ? '+' : ''}${_subtitleDelaySec.toStringAsFixed(1)}s",
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w600,
                color: _subtitleDelaySec != 0.0 ? const Color(0xFF38BDF8) : const Color(0xFFCBD5E1),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // --- Tezlik tanlash menyusi ---
  Widget _buildSpeedSelector() {
    const speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0];

    return PopupMenuButton<double>(
      tooltip: "Ijro tezligi ([ / ])",
      initialValue: _rate,
      onSelected: _setRate,
      color: const Color(0xFF1E293B),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: Color(0xFF334155)),
      ),
      itemBuilder: (ctx) => [
        for (final s in speeds)
          PopupMenuItem<double>(
            value: s,
            height: 36,
            child: Row(
              children: [
                Icon(
                  (s - _rate).abs() < 0.05 ? Icons.check_rounded : null,
                  size: 15,
                  color: const Color(0xFF38BDF8),
                ),
                const SizedBox(width: 8),
                Text(
                  s == 1.0 ? "1.0x (Normal)" : "${s}x",
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: (s - _rate).abs() < 0.05 ? FontWeight.bold : FontWeight.normal,
                    color: (s - _rate).abs() < 0.05 ? Colors.white : const Color(0xFFCBD5E1),
                  ),
                ),
              ],
            ),
          ),
      ],
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
        decoration: BoxDecoration(
          color: _rate != 1.0 ? const Color(0xFF38BDF8).withValues(alpha: 0.2) : Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: _rate != 1.0 ? const Color(0xFF38BDF8).withValues(alpha: 0.5) : Colors.white.withValues(alpha: 0.12),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.speed_rounded, size: 13, color: Color(0xFFCBD5E1)),
            const SizedBox(width: 4),
            Text(
              "${_rate.toStringAsFixed(1)}x",
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w600,
                color: _rate != 1.0 ? const Color(0xFF38BDF8) : const Color(0xFFCBD5E1),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // --- A-B Takrorlash tugmasi ---
  Widget _buildABLoopButton() {
    final hasA = _loopA != null;
    final hasAB = _loopA != null && _loopB != null;

    String label = "A-B";
    if (hasAB) {
      label = "A-B Sikl";
    } else if (hasA) {
      label = "[A: ${_formatDuration(_loopA!)}]";
    }

    return Tooltip(
      message: hasAB
          ? "A-B Takrorlashni to'xtatish (R)"
          : (hasA ? "B nuqtani belgilash (R)" : "A nuqtani belgilash (R)"),
      child: InkWell(
        onTap: _toggleABLoop,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
          decoration: BoxDecoration(
            color: hasAB
                ? const Color(0xFF38BDF8).withValues(alpha: 0.25)
                : (hasA ? Colors.amberAccent.withValues(alpha: 0.2) : Colors.white.withValues(alpha: 0.06)),
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: hasAB
                  ? const Color(0xFF38BDF8)
                  : (hasA ? Colors.amberAccent : Colors.white.withValues(alpha: 0.12)),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                hasAB ? Icons.repeat_rounded : Icons.repeat_one_rounded,
                size: 13,
                color: hasAB ? const Color(0xFF38BDF8) : (hasA ? Colors.amberAccent : const Color(0xFFCBD5E1)),
              ),
              const SizedBox(width: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 10.5,
                  fontWeight: FontWeight.w600,
                  color: hasAB ? const Color(0xFF38BDF8) : (hasA ? Colors.amberAccent : const Color(0xFFCBD5E1)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
