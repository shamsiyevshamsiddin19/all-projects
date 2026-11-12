import 'dart:async';
import 'dart:convert';
import 'dart:io';

class ProcessorCancelled implements Exception {
  const ProcessorCancelled();
}

class ProcessorTransportProgress {
  const ProcessorTransportProgress(this.message, this.progress);
  final String message;
  final double progress;
}

/// Isolates process startup, JSON framing, cancellation and secret lifetime.
/// A fake can implement this boundary without launching Python in widget tests.
abstract class ProcessorTransport {
  Future<Map<String, dynamic>> runJson(List<String> arguments);
  Future<Map<String, dynamic>> streamJson(
    List<String> arguments, {
    required void Function(ProcessorTransportProgress progress) onProgress,
  });
  Future<void> cancel();
}

class _SecretLease {
  const _SecretLease(this.file, this.directory);
  final File file;
  final Directory directory;
  Future<void> dispose() async {
    try {
      await directory.delete(recursive: true);
    } catch (_) {}
  }
}

class _StartedProcess {
  const _StartedProcess(this.process, this.lease);
  final Process process;
  final _SecretLease? lease;
}

class LocalProcessorTransport implements ProcessorTransport {
  LocalProcessorTransport({
    required this.root,
    required Map<String, String> Function() environment,
  }) : _configuredEnvironment = environment;

  final Directory root;
  final Map<String, String> Function() _configuredEnvironment;
  Process? _active;
  bool _cancelled = false;
  static String? _cachedPython;
  static const _keyNames = {
    'GROQ_API_KEY',
    'OPENAI_API_KEY',
    'GEMINI_API_KEY',
    'ANTHROPIC_API_KEY',
  };
  static final _sensitiveName = RegExp(
    r'(?:^|_)(?:API_KEY|TOKEN|SECRET|PASSWORD)$',
    caseSensitive: false,
  );
  static const _gracePeriod = Duration(seconds: 4);

  File get _script =>
      File('${root.path}${Platform.pathSeparator}desktop_processor.py');
  File? get _frozen {
    final file = File(
      '${root.path}${Platform.pathSeparator}desktop_processor${Platform.isWindows ? '.exe' : ''}',
    );
    return file.existsSync() ? file : null;
  }

  @override
  Future<Map<String, dynamic>> runJson(List<String> arguments) async {
    final result = await _run(arguments);
    return parseProcessorJsonOutput(
      stdout: result.stdout.toString(),
      stderr: result.stderr.toString(),
      exitCode: result.exitCode,
      arguments: arguments,
    );
  }

  @override
  Future<Map<String, dynamic>> streamJson(
    List<String> arguments, {
    required void Function(ProcessorTransportProgress progress) onProgress,
  }) async {
    final started = await _start(arguments);
    _active = started.process;
    _cancelled = false;
    try {
      return await _consume(started.process, onProgress);
    } finally {
      _active = null;
      await started.lease?.dispose();
    }
  }

  @override
  Future<void> cancel() async {
    final process = _active;
    if (process == null) return;
    _cancelled = true;
    if (Platform.isWindows) {
      try {
        await Process.run('taskkill', ['/PID', '${process.pid}', '/T', '/F']);
      } catch (_) {
        process.kill(ProcessSignal.sigkill);
      }
      return;
    }
    final exited = process.exitCode;
    var stopped = false;
    exited.whenComplete(() => stopped = true);
    await _signal('-TERM', process.pid);
    await Future.any([exited, Future<void>.delayed(_gracePeriod)]);
    if (!stopped) {
      await _signal('-KILL', process.pid);
      process.kill(ProcessSignal.sigkill);
    }
  }

  Future<_SecretLease?> _secretLease() async {
    final configured = _configuredEnvironment();
    if (configured.isEmpty) return null;
    final directory = await Directory.systemTemp.createTemp('subtitr-secrets-');
    try {
      await _restrict(directory.path, '700');
      final file = File('${directory.path}${Platform.pathSeparator}keys.json');
      await file.create(exclusive: true);
      await _restrict(file.path, '600');
      await file.writeAsString(
        jsonEncode({
          for (final name in _keyNames) name: configured[name] ?? '',
        }),
        flush: true,
      );
      return _SecretLease(file, directory);
    } catch (_) {
      try {
        await directory.delete(recursive: true);
      } catch (_) {}
      rethrow;
    }
  }

  Future<void> _restrict(String path, String mode) async {
    if (Platform.isWindows) return;
    if ((await Process.run('chmod', [mode, path])).exitCode != 0) {
      throw StateError('Vaqtinchalik kalit fayli himoyalanmadi');
    }
  }

  Map<String, String> _environment({
    bool ownGroup = false,
    _SecretLease? lease,
  }) {
    final result = <String, String>{
      for (final entry in Platform.environment.entries)
        if (!_sensitiveName.hasMatch(entry.key)) entry.key: entry.value,
    };
    for (final entry in _configuredEnvironment().entries) {
      if (!_keyNames.contains(entry.key) &&
          !_sensitiveName.hasMatch(entry.key)) {
        result[entry.key] = entry.value;
      }
    }
    if (lease != null) result['SUBTITR_SECRETS_FILE'] = lease.file.path;
    if (ownGroup) result['SUBTITR_OWN_PROCESS_GROUP'] = '1';
    return result;
  }

  Future<ProcessResult> _run(List<String> args) async {
    final lease = await _secretLease();
    try {
      final frozen = _frozen;
      final executable = frozen?.path ?? await _python();
      return await Process.run(
        executable,
        frozen == null ? [_script.path, ...args] : args,
        workingDirectory: root.path,
        runInShell: frozen == null && Platform.isWindows,
        environment: _environment(lease: lease),
        stdoutEncoding: utf8,
        stderrEncoding: utf8,
      );
    } finally {
      await lease?.dispose();
    }
  }

  Future<_StartedProcess> _start(List<String> args) async {
    final lease = await _secretLease();
    try {
      final frozen = _frozen;
      final process = await Process.start(
        frozen?.path ?? await _python(),
        frozen == null ? [_script.path, ...args] : args,
        workingDirectory: root.path,
        runInShell: frozen == null && Platform.isWindows,
        environment: _environment(ownGroup: true, lease: lease),
      );
      return _StartedProcess(process, lease);
    } catch (_) {
      await lease?.dispose();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> _consume(
    Process process,
    void Function(ProcessorTransportProgress) onProgress,
  ) async {
    Map<String, dynamic>? done;
    String? error;
    final stderrFuture = process.stderr.transform(utf8.decoder).join();
    await for (final line
        in process.stdout
            .transform(utf8.decoder)
            .transform(const LineSplitter())) {
      final event = parseProcessorEvent(line);
      if (event == null) continue;
      switch (event['type']) {
        case 'progress':
          onProgress(
            ProcessorTransportProgress(
              event['message'] as String? ?? '',
              (event['progress'] as num?)?.toDouble() ?? 0,
            ),
          );
        case 'done':
          done = event;
        case 'error':
          error = event['message'] as String? ?? "Noma'lum xato";
      }
    }
    final stderr = await stderrFuture;
    final code = await process.exitCode;
    if (_cancelled) throw const ProcessorCancelled();
    if (code != 0 || error != null) {
      throw StateError(
        error ?? stderr.trim().ifEmpty('Jarayon xato bilan tugadi'),
      );
    }
    return done ?? (throw StateError(stderr.trim().ifEmpty('Natija kelmadi')));
  }

  Future<void> _signal(String signal, int pid) async {
    try {
      if ((await Process.run('kill', [signal, '-$pid'])).exitCode == 0) return;
    } catch (_) {}
    try {
      await Process.run('kill', [signal, '$pid']);
    } catch (_) {
      if (signal == '-KILL') _active?.kill(ProcessSignal.sigkill);
    }
  }

  Future<String> _python() async {
    if (_cachedPython != null) return _cachedPython!;
    final sep = Platform.pathSeparator;
    final venv = Platform.isWindows
        ? '${root.path}$sep.venv${sep}Scripts${sep}python.exe'
        : '${root.path}$sep.venv${sep}bin${sep}python';
    if (File(venv).existsSync()) {
      return _cachedPython = venv;
    }
    for (final executable in ['python3', 'python']) {
      try {
        if ((await Process.run(executable, [
              '--version',
            ], runInShell: Platform.isWindows)).exitCode ==
            0) {
          return _cachedPython = executable;
        }
      } catch (_) {}
    }
    return _cachedPython = 'python3';
  }
}

Map<String, dynamic> parseProcessorJsonOutput({
  required String stdout,
  required String stderr,
  required int exitCode,
  required List<String> arguments,
}) {
  final line = const LineSplitter()
      .convert(stdout)
      .reversed
      .firstWhere((line) => line.trim().startsWith('{'), orElse: () => '');
  if (line.isEmpty) {
    throw ProcessException('desktop_processor', arguments, stderr, exitCode);
  }
  final decoded = jsonDecode(line);
  if (decoded is! Map) {
    throw const FormatException('Processor JSON obyekt emas');
  }
  final result = Map<String, dynamic>.from(decoded);
  if (result['type'] == 'error') {
    throw StateError(result['message'] as String? ?? "Noma'lum xato");
  }
  return result;
}

Map<String, dynamic>? parseProcessorEvent(String line) {
  if (!line.trim().startsWith('{')) return null;
  final decoded = jsonDecode(line);
  return decoded is Map ? Map<String, dynamic>.from(decoded) : null;
}

extension on String {
  String ifEmpty(String fallback) => isEmpty ? fallback : this;
}
