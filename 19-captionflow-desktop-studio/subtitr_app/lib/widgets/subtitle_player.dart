import 'dart:io';

import 'package:flutter/material.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

/// Video player for the translation editor, with the job's real subtitles.
///
/// mpv renders ASS through libass, the same library ffmpeg uses for the burn,
/// so what plays here is what gets burned — font, yellow box, position and
/// the floating vocabulary cards included. There is no second rendering path
/// to keep in sync.
///
/// If the player cannot start (no libmpv at runtime, an unsupported codec)
/// [onUnavailable] fires so the editor can fall back to the still frame,
/// which needs nothing but ffmpeg.
class SubtitlePlayer extends StatefulWidget {
  const SubtitlePlayer({
    super.key,
    required this.videoPath,
    required this.subtitlePath,
    required this.controller,
    this.onUnavailable,
  });

  final String videoPath;
  final String subtitlePath;
  final SubtitlePlayerController controller;
  final void Function(Object error)? onUnavailable;

  @override
  State<SubtitlePlayer> createState() => _SubtitlePlayerState();
}

/// Lets the editor drive the player without owning it.
class SubtitlePlayerController {
  _SubtitlePlayerState? _state;

  /// Jumps to [at] and starts playing from there.
  Future<void> seek(Duration at) async => _state?._seek(at);

  Future<void> pause() async => _state?._player?.pause();
}

class _SubtitlePlayerState extends State<SubtitlePlayer> {
  Player? _player;
  VideoController? _video;
  bool _ready = false;

  @override
  void initState() {
    super.initState();
    widget.controller._state = this;
    _start();
  }

  Future<void> _start() async {
    try {
      final player = Player();
      final video = VideoController(player);
      // play: false — ochilganda o'z-o'zidan o'ynamasin; foydalanuvchi
      // qatorni bosganda boshlanadi.
      await player.open(Media(Uri.file(widget.videoPath).toString()), play: false);
      await player.setSubtitleTrack(
        SubtitleTrack.uri(Uri.file(widget.subtitlePath).toString()),
      );
      if (!mounted) {
        await player.dispose();
        return;
      }
      setState(() {
        _player = player;
        _video = video;
        _ready = true;
      });
    } catch (error) {
      if (mounted) widget.onUnavailable?.call(error);
    }
  }

  Future<void> _seek(Duration at) async {
    final player = _player;
    if (player == null) return;
    await player.seek(at);
    await player.play();
  }

  @override
  void dispose() {
    widget.controller._state = null;
    // Pleyer libmpv jarayonini ushlab turadi — yopilmasa ovoz davom etadi.
    _player?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready || _video == null) {
      return const Center(
        child: SizedBox(
          width: 22,
          height: 22,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      );
    }
    return Video(controller: _video!, controls: AdaptiveVideoControls);
  }
}

/// True when the player's runtime dependency is present.
///
/// On Linux media_kit needs the system libmpv; everywhere else the libs ship
/// with the package. Checked before building the widget so the editor can go
/// straight to the still frame rather than flashing a broken player.
bool get playerAvailable {
  if (!Platform.isLinux) return true;
  for (final path in const [
    '/usr/lib/x86_64-linux-gnu/libmpv.so.2',
    '/usr/lib/x86_64-linux-gnu/libmpv.so',
    '/usr/lib64/libmpv.so.2',
    '/usr/lib/libmpv.so.2',
  ]) {
    if (File(path).existsSync()) return true;
  }
  return false;
}
