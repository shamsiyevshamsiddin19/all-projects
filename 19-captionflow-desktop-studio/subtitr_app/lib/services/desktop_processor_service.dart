import 'dart:convert';
import 'dart:io';

import 'processor_session_store.dart';
import 'processor_transport.dart';

export 'processor_transport.dart' show ProcessorCancelled;

class DesktopVideo {
  const DesktopVideo({
    required this.name,
    required this.path,
    required this.size,
    required this.subtitleName,
    required this.subtitlePath,
    this.isDir = false,
  });

  final String name;
  final String path;
  final int size;
  final String subtitleName;

  /// Video yonidan topilgan subtitrning to'liq yo'li. Nomning o'zi renderga
  /// yetmaydi: processor import qilishi uchun aynan shu manzil kerak.
  final String subtitlePath;
  final bool isDir;

  factory DesktopVideo.fromJson(Map<String, dynamic> json) {
    return DesktopVideo(
      name: json['name'] as String? ?? '',
      path: json['path'] as String? ?? '',
      size: json['size'] as int? ?? 0,
      subtitleName: json['subtitleName'] as String? ?? '',
      subtitlePath: json['subtitle'] as String? ?? '',
      isDir: json['isDir'] as bool? ?? false,
    );
  }
}

class ProcessorOutput {
  const ProcessorOutput({
    required this.kind,
    required this.label,
    required this.path,
    required this.name,
  });

  final String kind;
  final String label;
  final String path;
  final String name;

  factory ProcessorOutput.fromJson(Map<String, dynamic> json) {
    return ProcessorOutput(
      kind: json['kind'] as String? ?? '',
      label: json['label'] as String? ?? '',
      path: json['path'] as String? ?? '',
      name: json['name'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
    'kind': kind,
    'label': label,
    'path': path,
    'name': name,
  };
}

class ProcessorResult {
  const ProcessorResult({
    required this.outputs,
    required this.transcriber,
    required this.translator,
    required this.sourceLang,
    required this.targetLang,
    required this.outDir,
    this.usage = const {},
  });

  final List<ProcessorOutput> outputs;
  final String transcriber;
  final String translator;
  final String sourceLang;
  final String targetLang;
  final String outDir;

  /// Haqiqatda ketgan AI so'rovlari: `whisper`, `rescan`, `translate`.
  /// Boshlashdan oldingi baho taxminiy — bu esa aniq son.
  final Map<String, int> usage;

  factory ProcessorResult.fromJson(Map<String, dynamic> json) {
    final rawOutputs = json['outputs'];
    return ProcessorResult(
      outputs: rawOutputs is List
          ? rawOutputs
                .whereType<Map>()
                .map(
                  (item) =>
                      ProcessorOutput.fromJson(Map<String, dynamic>.from(item)),
                )
                .toList()
          : const [],
      transcriber: json['transcriber'] as String? ?? '',
      translator: json['translator'] as String? ?? '',
      sourceLang: json['sourceLang'] as String? ?? '',
      targetLang: json['targetLang'] as String? ?? '',
      outDir: json['outDir'] as String? ?? '',
      usage: switch (json['usage']) {
        final Map<dynamic, dynamic> m => {
          for (final e in m.entries)
            if (e.value is num) '${e.key}': (e.value as num).toInt(),
        },
        _ => const <String, int>{},
      },
    );
  }

  Map<String, dynamic> toJson() => {
    'outputs': outputs.map((o) => o.toJson()).toList(),
    'transcriber': transcriber,
    'translator': translator,
    'sourceLang': sourceLang,
    'targetLang': targetLang,
    'outDir': outDir,
    'usage': usage,
  };
}

/// One subtitle line — the original text plus its (editable) translation.
class SubtitleSegment {
  SubtitleSegment({
    required this.start,
    required this.end,
    required this.original,
    required this.translated,
    this.confidence,
  });

  double start;
  double end;
  String original;
  String translated;

  /// How sure the model was about this line (0..1), or null when unknown —
  /// a ready-made .srt or an embedded subtitle track carries no score.
  final double? confidence;

  /// Lines the model was unsure of. These are where a misheard name or a
  /// wrong word tends to be, so the editor flags them instead of leaving
  /// the user to hunt through every line.
  static const lowConfidence = 0.5;

  bool get isUncertain => confidence != null && confidence! < lowConfidence;

  factory SubtitleSegment.fromJson(Map<String, dynamic> json) {
    return SubtitleSegment(
      start: (json['start'] as num?)?.toDouble() ?? 0.0,
      end: (json['end'] as num?)?.toDouble() ?? 0.0,
      original: json['original'] as String? ?? '',
      translated: json['translated'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'start': start,
    'end': end,
    'original': original,
    'translated': translated,
    if (confidence != null) 'confidence': confidence,
  };
}

/// Result of the `prepare` phase: transcription + translation ready to review
/// and edit before the (slow) render/burn step.
class PreparedSession {
  const PreparedSession({
    required this.sessionPath,
    required this.video,
    required this.mode,
    required this.sourceLang,
    required this.targetLang,
    required this.transcriber,
    required this.translator,
    required this.segments,
    required this.vocabCount,
  });

  final String sessionPath;
  final String video;
  final String mode;
  final String sourceLang;
  final String targetLang;
  final String transcriber;
  final String translator;
  final List<SubtitleSegment> segments;
  final int vocabCount;

  factory PreparedSession.fromJson(Map<String, dynamic> json) {
    final rawSegments = json['segments'];
    return PreparedSession(
      sessionPath: json['session'] as String? ?? '',
      video: json['video'] as String? ?? '',
      mode: json['mode'] as String? ?? '',
      sourceLang: json['sourceLang'] as String? ?? '',
      targetLang: json['targetLang'] as String? ?? '',
      transcriber: json['transcriber'] as String? ?? '',
      translator: json['translator'] as String? ?? '',
      segments: rawSegments is List
          ? rawSegments
                .whereType<Map>()
                .map(
                  (item) =>
                      SubtitleSegment.fromJson(Map<String, dynamic>.from(item)),
                )
                .toList()
          : <SubtitleSegment>[],
      vocabCount: json['vocabCount'] as int? ?? 0,
    );
  }
}

/// The response from a single-line AI translation request.
class RetranslatedSegment {
  const RetranslatedSegment({
    required this.index,
    required this.translated,
    required this.provider,
  });

  final int index;
  final String translated;
  final String provider;

  factory RetranslatedSegment.fromJson(Map<String, dynamic> json) =>
      RetranslatedSegment(
        index: (json['index'] as num?)?.toInt() ?? -1,
        translated: json['translated'] as String? ?? '',
        provider: json['provider'] as String? ?? '',
      );
}

/// One section of the on-disk cache, as reported by `cache-info`.
class CacheSection {
  const CacheSection({
    required this.name,
    required this.label,
    required this.path,
    required this.bytes,
  });

  final String name;
  final String label;
  final String path;
  final int bytes;

  factory CacheSection.fromJson(Map<String, dynamic> json) => CacheSection(
    name: json['name'] as String? ?? '',
    label: json['label'] as String? ?? '',
    path: json['path'] as String? ?? '',
    bytes: (json['bytes'] as num?)?.toInt() ?? 0,
  );
}

/// How much disk the app's hidden working folders use. Shown in settings so
/// the download cache cannot quietly grow to tens of gigabytes unnoticed.
class CacheUsage {
  const CacheUsage({
    required this.sections,
    required this.total,
    this.freed = 0,
  });

  final List<CacheSection> sections;
  final int total;

  /// Bytes reclaimed by the call that produced this snapshot (0 for a read).
  final int freed;

  static const empty = CacheUsage(sections: [], total: 0);

  factory CacheUsage.fromJson(Map<String, dynamic> json) {
    final raw = json['sections'];
    return CacheUsage(
      sections: raw is List
          ? raw
                .whereType<Map>()
                .map((e) => CacheSection.fromJson(Map<String, dynamic>.from(e)))
                .toList()
          : const [],
      total: (json['total'] as num?)?.toInt() ?? 0,
      freed: (json['freed'] as num?)?.toInt() ?? 0,
    );
  }

  /// "1.4 GB" / "830 MB" / "0 MB" — always a round, readable figure.
  static String format(int bytes) {
    if (bytes >= 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
    }
    return '${(bytes / (1024 * 1024)).round()} MB';
  }
}

class ScanResult {
  const ScanResult({
    required this.videos,
    required this.kinoDir,
    required this.outDir,
  });

  final List<DesktopVideo> videos;
  final String kinoDir;
  final String outDir;
}

class ProcessorProgress {
  const ProcessorProgress({required this.message, required this.progress});

  final String message;
  final double progress;
}

/// A remote item returned by yt-dlp's lightweight playlist inspection.
/// It is metadata only: no video is downloaded until the user selects it.
class PlaylistEntry {
  const PlaylistEntry({
    required this.id,
    required this.title,
    required this.url,
    this.duration = '',
  });

  final String id;
  final String title;
  final String url;
  final String duration;

  factory PlaylistEntry.fromJson(Map<String, dynamic> json) => PlaylistEntry(
    id: json['id'] as String? ?? '',
    title: json['title'] as String? ?? 'Nomsiz video',
    url: json['url'] as String? ?? '',
    duration: json['duration'] as String? ?? '',
  );
}

class DesktopProcessorService {
  DesktopProcessorService({
    Directory? root,
    ProcessorTransport? transport,
    ProcessorSessionStore? sessionStore,
  }) : root = root ?? _findRoot(),
       _sessionStore = sessionStore ?? const ProcessorSessionStore() {
    _transport =
        transport ??
        LocalProcessorTransport(
          root: this.root,
          environment: () => processEnvironment,
        );
  }

  final Directory root;
  final ProcessorSessionStore _sessionStore;
  late final ProcessorTransport _transport;

  /// Provider settings received from the in-app settings screen.
  ///
  /// The public shape stays an environment-like map for backwards
  /// compatibility. API keys in it are deliberately NOT passed as process
  /// environment variables: they travel in an owner-only temporary file.
  Map<String, String> processEnvironment = const {};

  File get script =>
      File('${root.path}${Platform.pathSeparator}desktop_processor.py');

  Future<ScanResult> scan({String? path}) async {
    final args = ['scan'];
    if (path != null) {
      args.addAll(['--dir', path]);
    }
    final payload = await _runJson(args);
    final rawVideos = payload['videos'];
    return ScanResult(
      videos: rawVideos is List
          ? rawVideos
                .whereType<Map>()
                .map(
                  (item) =>
                      DesktopVideo.fromJson(Map<String, dynamic>.from(item)),
                )
                .toList()
          : const [],
      kinoDir:
          payload['kinoDir'] as String? ??
          '${root.path}${Platform.pathSeparator}Kinolar',
      outDir:
          payload['outDir'] as String? ??
          '${root.path}${Platform.pathSeparator}Tayyor natijalar',
    );
  }

  Future<void> installDependencies({
    required void Function(ProcessorProgress progress) onProgress,
  }) async {
    await _streamProcess(['install-deps'], onProgress: onProgress);
  }

  /// Self-updates the bundled yt-dlp binary (`yt-dlp -U`). Movie/video sites
  /// change often, so keeping the downloader fresh keeps downloads working.
  /// Fire-and-forget: never throws — a stale downloader is better than a crash.
  Future<bool> updateYtDlp() async {
    try {
      final payload = await _runJson(['update-ytdlp']);
      return payload['updated'] == true;
    } catch (_) {
      return false;
    }
  }

  /// Reads how much disk the hidden cache folders use (downloads, work files,
  /// finished transcripts, Whisper models).
  Future<CacheUsage> cacheInfo() async {
    return CacheUsage.fromJson(await _runJson(['cache-info']));
  }

  /// Deletes a cache section and returns the usage afterwards. Defaults to
  /// `downloads` — the section that grows fastest and costs nothing but a
  /// re-download. `transcripts` is never part of `all`: throwing away finished
  /// translations means paying the AI for them again.
  Future<CacheUsage> clearCache({String what = 'downloads'}) async {
    return CacheUsage.fromJson(await _runJson(['clear-cache', '--what', what]));
  }

  /// Where the processor writes its daily log. Used by the settings screen so
  /// the user (or a bug report) can get at the full traceback — the GUI only
  /// ever shows a one-line error.
  Future<String> logDir() async {
    final payload = await _runJson(['log-path']);
    return payload['dir'] as String? ?? '';
  }

  Future<ProcessorResult> process({
    required String videoPath,
    required String mode,
    required String sourceLang,
    required String targetLang,
    required void Function(ProcessorProgress progress) onProgress,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
    String origStyle = 'box',
    String quality = '1080',
    bool upscale = false,
    String? subtitlePath,
    double subtitleOffset = 0,
    String? voice,
    double ducking = 0.18,
  }) async {
    final payload = await _streamProcess([
      'process',
      '--video',
      videoPath,
      '--mode',
      mode,
      '--source-lang',
      sourceLang,
      '--target-lang',
      targetLang,
      '--font-scale',
      fontScale.toString(),
      '--position',
      position,
      '--sub-color',
      subColor,
      '--orig-style',
      origStyle,
      '--quality',
      quality,
      if (upscale) '--upscale',
      if (subtitlePath != null && subtitlePath.isNotEmpty) ...[
        '--subtitle',
        subtitlePath,
      ],
      if (subtitleOffset != 0) ...[
        '--subtitle-offset',
        subtitleOffset.toString(),
      ],
      if (voice != null && voice.isNotEmpty) ...['--voice', voice],
      if (ducking != 0.18) ...['--ducking', ducking.toString()],
    ], onProgress: onProgress);
    return ProcessorResult.fromJson(payload);
  }

  /// Phase 1 of the review-before-render flow: transcribe + translate + build
  /// vocab, then STOP before rendering. Returns the segments to review/edit.
  Future<PreparedSession> prepare({
    required String videoPath,
    required String mode,
    required String sourceLang,
    required String targetLang,
    required void Function(ProcessorProgress progress) onProgress,
    String? subtitlePath,
    double subtitleOffset = 0,
    String? voice,
    double ducking = 0.18,
  }) async {
    final payload = await _streamProcess([
      'prepare',
      '--video',
      videoPath,
      '--mode',
      mode,
      '--source-lang',
      sourceLang,
      '--target-lang',
      targetLang,
      if (subtitlePath != null && subtitlePath.isNotEmpty) ...[
        '--subtitle',
        subtitlePath,
      ],
      if (subtitleOffset != 0) ...[
        '--subtitle-offset',
        subtitleOffset.toString(),
      ],
      if (voice != null && voice.isNotEmpty) ...['--voice', voice],
      if (ducking != 0.18) ...['--ducking', ducking.toString()],
    ], onProgress: onProgress);
    return PreparedSession.fromJson(payload);
  }

  /// Writes the session's ASS subtitle file and returns it together with the
  /// video path.
  ///
  /// mpv draws ASS with libass itself, so handing it this file makes the
  /// in-editor player show subtitles exactly as they will be burned — no
  /// separate rendering path to keep in sync.
  Future<({String subtitles, String video})> subtitleFile({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required String mode,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
    String origStyle = 'box',
  }) async {
    final stamp = DateTime.now().microsecondsSinceEpoch;
    final sep = Platform.pathSeparator;
    final edits = File(
      '${Directory.systemTemp.path}${sep}subtitr_edits_$stamp.json',
    );
    final out = File(
      '${Directory.systemTemp.path}${sep}subtitr_live_$stamp.ass',
    );
    await edits.writeAsString(
      jsonEncode(segments.map((s) => s.toJson()).toList()),
    );
    try {
      final payload = await _runJson([
        'subtitle-file',
        '--session',
        sessionPath,
        '--segments',
        edits.path,
        '--out',
        out.path,
        '--render-mode',
        mode,
        '--font-scale',
        fontScale.toString(),
        '--position',
        position,
        '--sub-color',
        subColor,
        '--orig-style',
        origStyle,
      ]);
      return (
        subtitles: payload['path'] as String? ?? out.path,
        video: payload['video'] as String? ?? '',
      );
    } finally {
      try {
        await edits.delete();
      } catch (_) {}
    }
  }

  /// Renders ONE frame at [at] seconds with the real subtitle drawn on it,
  /// and returns the image path.
  ///
  /// The frame is built from the same ASS the burn uses, so what the editor
  /// shows is what the finished video will look like — font, yellow box,
  /// position and vocabulary card included. Previously the only way to see
  /// any of that was to wait for a full render.
  Future<String> previewFrame({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required double at,
    required String mode,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
    String origStyle = 'box',
  }) async {
    final stamp = DateTime.now().microsecondsSinceEpoch;
    final sep = Platform.pathSeparator;
    final edits = File(
      '${Directory.systemTemp.path}${sep}subtitr_prev_$stamp.json',
    );
    final out = File(
      '${Directory.systemTemp.path}${sep}subtitr_prev_$stamp.jpg',
    );
    await edits.writeAsString(
      jsonEncode(segments.map((s) => s.toJson()).toList()),
    );
    try {
      final payload = await _runJson([
        'preview',
        '--session',
        sessionPath,
        '--segments',
        edits.path,
        '--at',
        at.toStringAsFixed(3),
        '--out',
        out.path,
        '--render-mode',
        mode,
        '--font-scale',
        fontScale.toString(),
        '--position',
        position,
        '--sub-color',
        subColor,
        '--orig-style',
        origStyle,
      ]);
      return payload['path'] as String? ?? out.path;
    } finally {
      try {
        await edits.delete();
      } catch (_) {}
    }
  }

  /// Phase 2: render the (possibly edited) segments from a prepared session and
  /// burn them into the video.
  Future<ProcessorResult> render({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required void Function(ProcessorProgress progress) onProgress,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
    String origStyle = 'box',
    String quality = '1080',
    bool upscale = false,
  }) async {
    // Write the edited segments next to the session so the processor can pick
    // them up (they fully replace the originals for rendering).
    final editsFile = File(
      '${Directory.systemTemp.path}${Platform.pathSeparator}'
      'subtitr_edits_${DateTime.now().millisecondsSinceEpoch}.json',
    );
    await editsFile.writeAsString(
      jsonEncode(segments.map((s) => s.toJson()).toList()),
    );
    try {
      final payload = await _streamProcess([
        'render',
        '--session',
        sessionPath,
        '--segments',
        editsFile.path,
        '--font-scale',
        fontScale.toString(),
        '--position',
        position,
        '--sub-color',
        subColor,
        '--orig-style',
        origStyle,
        '--quality',
        quality,
        if (upscale) '--upscale',
      ], onProgress: onProgress);
      return ProcessorResult.fromJson(payload);
    } finally {
      try {
        await editsFile.delete();
      } catch (_) {}
    }
  }

  /// Downloads a video from a URL (YouTube/Instagram/movie sites) WITHOUT
  /// processing it — saves the raw video to a visible folder. Returns the
  /// output info (path, name, dir).
  Future<Map<String, dynamic>> downloadUrl({
    required String url,
    required void Function(ProcessorProgress progress) onProgress,
    String quality = '1080',
  }) async {
    return _streamProcess([
      'download',
      '--url',
      url,
      '--quality',
      quality,
    ], onProgress: onProgress);
  }

  /// Lists at most [limit] playlist/channel entries without downloading them.
  /// Selected entries are subsequently run one-by-one, preserving cancellation
  /// and per-video failure reporting in the desktop queue.
  Future<List<PlaylistEntry>> playlist({
    required String url,
    int limit = 25,
  }) async {
    final payload = await _runJson([
      'playlist',
      '--url',
      url,
      '--limit',
      '$limit',
    ]);
    final raw = payload['entries'];
    return raw is List
        ? raw
              .whereType<Map>()
              .map(
                (item) =>
                    PlaylistEntry.fromJson(Map<String, dynamic>.from(item)),
              )
              .where((e) => e.url.isNotEmpty)
              .toList()
        : const [];
  }

  /// Resolves a bundled tool (ffmpeg/ffprobe) next to the app, else PATH.
  String resolveTool(String name) {
    final sep = Platform.pathSeparator;
    final fname = '$name${Platform.isWindows ? '.exe' : ''}';
    for (final base in ['${root.path}$sep', '${root.path}${sep}tools$sep']) {
      final bundled = File('$base$fname');
      if (bundled.existsSync()) {
        return bundled.path;
      }
    }
    return name;
  }

  /// Video duration in seconds via ffprobe (0 on any failure).
  Future<double> probeDuration(String path) async {
    if (path.isEmpty) return 0.0;
    try {
      final result = await Process.run(resolveTool('ffprobe'), [
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        path,
      ], runInShell: false);
      if (result.exitCode == 0) {
        return double.tryParse(result.stdout.toString().trim()) ?? 0.0;
      }
    } catch (_) {}
    return 0.0;
  }

  Future<void> openPath(String path) async {
    if (path.isEmpty) {
      return;
    }
    if (Platform.isWindows) {
      await Process.run('explorer', [path], runInShell: true);
      return;
    }
    if (Platform.isMacOS) {
      await Process.run('open', [path]);
      return;
    }
    await Process.run('xdg-open', [path]);
  }

  Future<Map<String, dynamic>> _runJson(List<String> args) =>
      _transport.runJson(args);

  Future<Map<String, dynamic>> _streamProcess(
    List<String> args, {
    required void Function(ProcessorProgress progress) onProgress,
  }) => _transport.streamJson(
    args,
    onProgress: (event) => onProgress(
      ProcessorProgress(message: event.message, progress: event.progress),
    ),
  );

  /// Aborts the active processor and its descendants when supported by the
  /// configured transport. Calling it while idle is harmless.
  Future<void> cancel() => _transport.cancel();

  static Directory _findRoot() {
    // The processor (desktop_processor.exe/.py) ships next to the app. Search
    // from the running executable's own directory first so we do not depend on
    // the shortcut's working directory, then fall back to the current dir (dev).
    final executableDirectory = File(Platform.resolvedExecutable).parent;
    // macOS paketi Python qatlamini `.app/Contents/Resources` ichida olib
    // yuradi. Bu release DMG'ni mustaqil qiladi: `.app` yonidagi tashqi
    // fayllar tasodifan o'chib ketsa ham protsessor topiladi.
    final macRuntime = Platform.isMacOS
        ? Directory(
            '${executableDirectory.parent.path}${Platform.pathSeparator}'
            'Resources${Platform.pathSeparator}SubtitrRuntime',
          )
        : null;
    final starts = <Directory>[
      ?macRuntime,
      executableDirectory,
      Directory.current.absolute,
    ];
    for (final start in starts) {
      var dir = start.absolute;
      for (var i = 0; i < 10; i++) {
        final pyFile = File(
          '${dir.path}${Platform.pathSeparator}desktop_processor.py',
        );
        final exeFile = File(
          '${dir.path}${Platform.pathSeparator}desktop_processor'
          '${Platform.isWindows ? '.exe' : ''}',
        );
        if (pyFile.existsSync() || exeFile.existsSync()) {
          return dir;
        }
        final parent = dir.parent;
        if (parent.path == dir.path) {
          break;
        }
        dir = parent;
      }
    }
    return Directory.current.absolute;
  }

  /// Asks the configured translator for just one edited subtitle line.
  Future<RetranslatedSegment> retranslate({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required int index,
  }) async {
    if (index < 0 || index >= segments.length) {
      throw ArgumentError.value(index, 'index', 'Mavjud subtitr qatori emas');
    }
    final edits = await _writeSegmentsTemp('subtitr_retranslate_', segments);
    try {
      final payload = await _streamProcess([
        'retranslate',
        '--session',
        sessionPath,
        '--segments',
        edits.path,
        '--index',
        index.toString(),
      ], onProgress: (_) {});
      return RetranslatedSegment.fromJson(payload);
    } finally {
      await _deleteQuietly(edits);
    }
  }

  /// Crash-safe local draft next to the prepared session.
  Future<void> saveDraft({
    required String sessionPath,
    required List<SubtitleSegment> segments,
  }) async {
    await _sessionStore.saveDraft(
      sessionPath: sessionPath,
      segments: segments.map((segment) => segment.toJson()).toList(),
    );
  }

  /// Returns a compatible saved draft, or null if missing/corrupt.
  Future<List<SubtitleSegment>?> loadDraft({
    required String sessionPath,
    required int expectedSegments,
  }) async {
    final draft = await _sessionStore.loadDraft(
      sessionPath: sessionPath,
      expectedSegments: expectedSegments,
    );
    return draft?.map(SubtitleSegment.fromJson).toList();
  }

  Future<void> discardDraft(String sessionPath) =>
      _sessionStore.deleteQuietly(_sessionStore.draftFile(sessionPath));

  Future<File> _writeSegmentsTemp(
    String prefix,
    List<SubtitleSegment> segments,
  ) async {
    return _sessionStore.writeSegments(
      prefix,
      segments.map((segment) => segment.toJson()).toList(),
    );
  }

  Future<void> _deleteQuietly(File file) async {
    await _sessionStore.deleteQuietly(file);
  }
}
