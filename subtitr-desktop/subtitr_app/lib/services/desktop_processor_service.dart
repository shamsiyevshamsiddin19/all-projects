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
}

class ProcessorResult {
  const ProcessorResult({
    required this.outputs,
    required this.transcriber,
    required this.translator,
    required this.sourceLang,
    required this.targetLang,
    required this.outDir,
  });

  final List<ProcessorOutput> outputs;
  final String transcriber;
  final String translator;
  final String sourceLang;
  final String targetLang;
  final String outDir;

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
    );
  }
}

/// One subtitle line — the original text plus its (editable) translation.
class SubtitleSegment {
  SubtitleSegment({
    required this.start,
    required this.end,
    required this.original,
    required this.translated,
  });

  final double start;
  final double end;
  String original;
  String translated;

  factory SubtitleSegment.fromJson(Map<String, dynamic> json) {
    return SubtitleSegment(
      start: (json['start'] as num?)?.toDouble() ?? 0.0,
      end: (json['end'] as num?)?.toDouble() ?? 0.0,
      original: json['original'] as String? ?? '',
      translated: json['translated'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'start': start,
        'end': end,
        'original': original,
        'translated': translated,
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

  Future<ProcessorResult> process({
    required String videoPath,
    required String mode,
    required String sourceLang,
    required String targetLang,
    required void Function(ProcessorProgress progress) onProgress,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
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

  /// Phase 2: render the (possibly edited) segments from a prepared session and
  /// burn them into the video.
  Future<ProcessorResult> render({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required void Function(ProcessorProgress progress) onProgress,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
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
  }) async {
    return _streamProcess(['download', '--url', url], onProgress: onProgress);
  }

  /// Resolves a bundled tool (ffmpeg/ffprobe) next to the app, else PATH.
  String resolveTool(String name) {
    final bundled = File(
      '${root.path}${Platform.pathSeparator}$name${Platform.isWindows ? '.exe' : ''}',
    );
    return bundled.existsSync() ? bundled.path : name;
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

  Map<String, String>? get _env =>
      processEnvironment.isEmpty ? null : processEnvironment;

  Future<ProcessResult> _executeRun(List<String> args) async {
    final exeFile = File('${root.path}${Platform.pathSeparator}desktop_processor.exe');
    if (exeFile.existsSync()) {
      return Process.run(
        exeFile.path,
        args,
        workingDirectory: root.path,
        runInShell: false,
        environment: _env,
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
      environment: _env,
      stdoutEncoding: utf8,
      stderrEncoding: utf8,
    );
  }

  Future<Process> _executeStart(List<String> args) async {
    final exeFile = File('${root.path}${Platform.pathSeparator}desktop_processor.exe');
    if (exeFile.existsSync()) {
      return Process.start(
        exeFile.path,
        args,
        workingDirectory: root.path,
        runInShell: false,
        environment: _env,
      );
    }
    final executable = await _pythonExecutable();
    return Process.start(
      executable,
      [script.path, ...args],
      workingDirectory: root.path,
      runInShell: Platform.isWindows,
      environment: _env,
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
  Future<void> cancel() async {
    final process = _active;
    if (process == null) return;
    _cancelled = true;
    if (Platform.isWindows) {
      // Kill the whole process tree — Process.kill() alone leaves ffmpeg running.
      try {
        await Process.run('taskkill', ['/PID', '${process.pid}', '/T', '/F']);
      } catch (_) {
        process.kill(ProcessSignal.sigkill);
      }
    } else {
      process.kill(ProcessSignal.sigkill);
    }
  }

  Future<Map<String, dynamic>> _streamProcess(
    List<String> args, {
    required void Function(ProcessorProgress progress) onProgress,
  }) async {
    final process = await _executeStart(args);
    _active = process;
    _cancelled = false;

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
    _active = null;
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

  static Future<String> _pythonExecutable() async {
    final python = await Process.run('python', [
      '--version',
    ], runInShell: Platform.isWindows);
    if (python.exitCode == 0) {
      return 'python';
    }
    return 'python';
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
          '${dir.path}${Platform.pathSeparator}desktop_processor.exe',
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
