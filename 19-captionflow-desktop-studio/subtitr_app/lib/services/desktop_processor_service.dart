import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Thrown when the user aborts a running job via [DesktopProcessorService.cancel].
class ProcessorCancelled implements Exception {
  const ProcessorCancelled();
}

typedef _CancelledException = ProcessorCancelled;

class DesktopVideo {
  const DesktopVideo({
    required this.name,
    required this.path,
    required this.size,
    required this.subtitleName,
    this.isDir = false,
  });

  final String name;
  final String path;
  final int size;
  final String subtitleName;
  final bool isDir;

  factory DesktopVideo.fromJson(Map<String, dynamic> json) {
    return DesktopVideo(
      name: json['name'] as String? ?? '',
      path: json['path'] as String? ?? '',
      size: json['size'] as int? ?? 0,
      subtitleName: json['subtitleName'] as String? ?? '',
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
              .map((item) =>
                  SubtitleSegment.fromJson(Map<String, dynamic>.from(item)))
              .toList()
          : <SubtitleSegment>[],
      vocabCount: json['vocabCount'] as int? ?? 0,
    );
  }
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
  const CacheUsage({required this.sections, required this.total, this.freed = 0});

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

class DesktopProcessorService {
  DesktopProcessorService() : root = _findRoot();

  final Directory root;

  /// Extra environment variables (API keys, model overrides) injected into the
  /// Python processor at launch. Populated from the in-app settings so no keys
  /// are ever hard-coded or shipped with the app.
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
    final edits = File('${Directory.systemTemp.path}${sep}subtitr_edits_$stamp.json');
    final out = File('${Directory.systemTemp.path}${sep}subtitr_live_$stamp.ass');
    await edits.writeAsString(
      jsonEncode(segments.map((s) => s.toJson()).toList()),
    );
    try {
      final payload = await _runJson([
        'subtitle-file',
        '--session', sessionPath,
        '--segments', edits.path,
        '--out', out.path,
        '--render-mode', mode,
        '--font-scale', fontScale.toString(),
        '--position', position,
        '--sub-color', subColor,
        '--orig-style', origStyle,
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
    final edits = File('${Directory.systemTemp.path}${sep}subtitr_prev_$stamp.json');
    final out = File('${Directory.systemTemp.path}${sep}subtitr_prev_$stamp.jpg');
    await edits.writeAsString(
      jsonEncode(segments.map((s) => s.toJson()).toList()),
    );
    try {
      final payload = await _runJson([
        'preview',
        '--session', sessionPath,
        '--segments', edits.path,
        '--at', at.toStringAsFixed(3),
        '--out', out.path,
        '--render-mode', mode,
        '--font-scale', fontScale.toString(),
        '--position', position,
        '--sub-color', subColor,
        '--orig-style', origStyle,
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
    return _streamProcess(
      ['download', '--url', url, '--quality', quality],
      onProgress: onProgress,
    );
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
      final result = await Process.run(
        resolveTool('ffprobe'),
        [
          '-v', 'error',
          '-show_entries', 'format=duration',
          '-of', 'default=noprint_wrappers=1:nokey=1',
          path,
        ],
        runInShell: false,
      );
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

  /// Environment for the processor. Dart merges this over the parent
  /// environment, so PATH and friends are still inherited.
  ///
  /// [ownGroup] is set for long-running jobs only: it tells the processor to
  /// put itself in its own process group so [cancel] can stop the whole tree
  /// (python + ffmpeg + yt-dlp) with one signal. It is deliberately NOT set
  /// for short commands, and never for plain CLI use, where it would stop
  /// Ctrl+C from reaching the process.
  Map<String, String>? _envFor({bool ownGroup = false}) {
    if (processEnvironment.isEmpty && !ownGroup) return null;
    return {
      ...processEnvironment,
      if (ownGroup) 'SUBTITR_OWN_PROCESS_GROUP': '1',
    };
  }

  /// The frozen (PyInstaller) processor shipped next to the app, or null when
  /// only the `.py` source is present. Windows builds carry the `.exe`
  /// suffix, Linux/macOS ones do not.
  File? get _frozenProcessor {
    final file = File(
      '${root.path}${Platform.pathSeparator}desktop_processor'
      '${Platform.isWindows ? '.exe' : ''}',
    );
    return file.existsSync() ? file : null;
  }

  Future<ProcessResult> _executeRun(List<String> args) async {
    final exeFile = _frozenProcessor;
    if (exeFile != null) {
      return Process.run(
        exeFile.path,
        args,
        workingDirectory: root.path,
        runInShell: false,
        environment: _envFor(),
        // The processor prints UTF-8 JSON; decode as UTF-8 so non-ASCII
        // folder/file names (Cyrillic, etc.) are not mangled by the OS ANSI
        // code page (the Process.run default).
        stdoutEncoding: utf8,
        stderrEncoding: utf8,
      );
    }
    final executable = await _pythonExecutable();
    return Process.run(
      executable,
      [script.path, ...args],
      workingDirectory: root.path,
      runInShell: Platform.isWindows,
      environment: _envFor(),
      stdoutEncoding: utf8,
      stderrEncoding: utf8,
    );
  }

  Future<Process> _executeStart(List<String> args) async {
    final exeFile = _frozenProcessor;
    if (exeFile != null) {
      return Process.start(
        exeFile.path,
        args,
        workingDirectory: root.path,
        runInShell: false,
        environment: _envFor(ownGroup: true),
      );
    }
    final executable = await _pythonExecutable();
    return Process.start(
      executable,
      [script.path, ...args],
      workingDirectory: root.path,
      runInShell: Platform.isWindows,
      environment: _envFor(ownGroup: true),
    );
  }

  Future<Map<String, dynamic>> _runJson(List<String> args) async {
    final result = await _executeRun(args);
    final lines = const LineSplitter().convert(result.stdout.toString());
    final jsonLine = lines.reversed.firstWhere(
      (line) => line.trim().startsWith('{'),
      orElse: () => '',
    );
    if (jsonLine.isEmpty) {
      throw ProcessException(
        'desktop_processor',
        args,
        result.stderr.toString(),
        result.exitCode,
      );
    }
    final payload = jsonDecode(jsonLine) as Map<String, dynamic>;
    if (payload['type'] == 'error') {
      throw StateError(payload['message'] as String? ?? "Noma'lum xato");
    }
    return payload;
  }

  Process? _active;
  bool _cancelled = false;

  /// Aborts the currently running job (kills the processor and its ffmpeg
  /// children). Safe to call when nothing is running.
  /// How long the processor gets to shut down cleanly before it is killed.
  static const _gracePeriod = Duration(seconds: 4);

  Future<void> cancel() async {
    final process = _active;
    if (process == null) return;
    _cancelled = true;

    if (Platform.isWindows) {
      // Windows has no graceful equivalent for a console-less child, so the
      // tree is killed outright. /T covers grandchildren (ffmpeg, yt-dlp).
      try {
        await Process.run('taskkill', ['/PID', '${process.pid}', '/T', '/F']);
      } catch (_) {
        process.kill(ProcessSignal.sigkill);
      }
      return;
    }

    // POSIX: SIGKILL cannot be caught, so it used to skip the processor's own
    // cleanup — a half-written .mp4 stayed in the output folder and the job's
    // temp dir (up to ~1 GB of WAV) stayed in the cache. Ask politely first:
    // the processor turns SIGTERM into KeyboardInterrupt, so its `finally`
    // blocks run. Only if it is still alive after the grace period do we kill.
    //
    // The signal goes to the whole process GROUP (negative pid) because
    // `pkill -P` reached direct children only — ffmpeg spawned by yt-dlp
    // survived as an orphan and kept burning CPU. The processor puts itself
    // in its own group when SUBTITR_OWN_PROCESS_GROUP is set (see
    // `core.install_signal_handlers`).
    final exited = process.exitCode;
    var stopped = false;
    exited.whenComplete(() => stopped = true);

    await _signal('-TERM', process.pid);
    await Future.any([
      exited,
      Future<void>.delayed(_gracePeriod),
    ]);
    if (stopped) return;

    await _signal('-KILL', process.pid);
    process.kill(ProcessSignal.sigkill);
  }

  /// Sends a signal to the processor's process group, falling back to the
  /// single process when the group send is not permitted.
  Future<void> _signal(String signal, int pid) async {
    try {
      final group = await Process.run('kill', [signal, '-$pid']);
      if (group.exitCode == 0) return;
    } catch (_) {
      // `kill` missing — fall through to the single-process path.
    }
    try {
      await Process.run('kill', [signal, '$pid']);
    } catch (_) {
      if (signal == '-KILL') _active?.kill(ProcessSignal.sigkill);
    }
  }

  Future<Map<String, dynamic>> _streamProcess(
    List<String> args, {
    required void Function(ProcessorProgress progress) onProgress,
  }) async {
    final process = await _executeStart(args);
    _active = process;
    _cancelled = false;
    try {
      return await _consume(process, onProgress);
    } finally {
      // Ilgari `_active = null` faqat muvaffaqiyatli yo'lda bajarilardi:
      // oqimda xato chiqsa o'lgan jarayon "faol" bo'lib qolar va keyingi
      // `cancel()` yo'q pid'ga signal yuborardi.
      _active = null;
    }
  }

  Future<Map<String, dynamic>> _consume(
    Process process,
    void Function(ProcessorProgress progress) onProgress,
  ) async {
    Map<String, dynamic>? donePayload;
    String? errorMessage;

    // Start reading stderr concurrently to avoid OS pipe buffer deadlock
    final stderrFuture = process.stderr.transform(utf8.decoder).join();

    await for (final line
        in process.stdout
            .transform(utf8.decoder)
            .transform(const LineSplitter())) {
      if (!line.trim().startsWith('{')) {
        continue;
      }
      final payload = jsonDecode(line) as Map<String, dynamic>;
      switch (payload['type']) {
        case 'progress':
          onProgress(
            ProcessorProgress(
              message: payload['message'] as String? ?? '',
              progress: (payload['progress'] as num?)?.toDouble() ?? 0,
            ),
          );
          break;
        case 'done':
          donePayload = payload;
          break;
        case 'error':
          errorMessage = payload['message'] as String? ?? "Noma'lum xato";
          break;
      }
    }

    final stderr = await stderrFuture;
    final code = await process.exitCode;
    if (_cancelled) {
      throw const _CancelledException();
    }
    if (code != 0 || errorMessage != null) {
      throw StateError(
        errorMessage ?? stderr.trim().ifEmpty('Jarayon xato bilan tugadi'),
      );
    }
    final payload = donePayload;
    if (payload == null) {
      throw StateError(stderr.trim().ifEmpty('Natija kelmadi'));
    }
    return payload;
  }

  static String? _cachedPython;

  /// Locates a usable Python interpreter. A virtualenv shipped next to the
  /// processor wins (its site-packages already hold groq/openai/gemini), then
  /// `python3` (the only name that exists on most Linux distros), then `python`.
  Future<String> _pythonExecutable() async {
    final cached = _cachedPython;
    if (cached != null) {
      return cached;
    }
    final sep = Platform.pathSeparator;
    final venv = Platform.isWindows
        ? '${root.path}$sep.venv${sep}Scripts${sep}python.exe'
        : '${root.path}$sep.venv${sep}bin${sep}python';
    if (File(venv).existsSync()) {
      return _cachedPython = venv;
    }
    for (final name in const ['python3', 'python']) {
      try {
        final probe = await Process.run(name, [
          '--version',
        ], runInShell: Platform.isWindows);
        if (probe.exitCode == 0) {
          return _cachedPython = name;
        }
      } catch (_) {
        // Not on PATH — try the next candidate.
      }
    }
    return _cachedPython = 'python3';
  }

  static Directory _findRoot() {
    // The processor (desktop_processor.exe/.py) ships next to the app. Search
    // from the running executable's own directory first so we do not depend on
    // the shortcut's working directory, then fall back to the current dir (dev).
    final starts = <Directory>[
      File(Platform.resolvedExecutable).parent,
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
}

extension on String {
  String ifEmpty(String fallback) => isEmpty ? fallback : this;
}
