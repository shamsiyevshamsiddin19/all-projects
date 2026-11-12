import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';
import 'package:subtitr_app/services/processor_session_store.dart';
import 'package:subtitr_app/services/processor_transport.dart';

class _FakeTransport implements ProcessorTransport {
  _FakeTransport({this.response = const {'type': 'done'}});

  final Map<String, dynamic> response;
  var cancelled = false;
  List<String>? streamedArguments;

  @override
  Future<void> cancel() async => cancelled = true;

  @override
  Future<Map<String, dynamic>> runJson(List<String> arguments) async =>
      response;

  @override
  Future<Map<String, dynamic>> streamJson(
    List<String> arguments, {
    required void Function(ProcessorTransportProgress progress) onProgress,
  }) async {
    streamedArguments = arguments;
    onProgress(const ProcessorTransportProgress('Ishlanmoqda', 0.5));
    return response;
  }
}

void main() {
  test('DesktopVideo parses scan JSON', () {
    final video = DesktopVideo.fromJson({
      'name': 'movie.mp4',
      'path': r'E:\Subtitle\Kinolar\movie.mp4',
      'size': 1024,
      'subtitleName': 'movie.srt',
      'subtitle': r'E:\Subtitle\Kinolar\movie.srt',
    });

    expect(video.name, 'movie.mp4');
    expect(video.size, 1024);
    expect(video.subtitleName, 'movie.srt');
    expect(video.subtitlePath, r'E:\Subtitle\Kinolar\movie.srt');
  });

  group('CacheUsage', () {
    test('parses the cache-info payload', () {
      final usage = CacheUsage.fromJson({
        'sections': [
          {
            'name': 'downloads',
            'label': 'Yuklab olingan videolar',
            'path': '/tmp/yuklamalar',
            'bytes': 870318080,
          },
          {
            'name': 'work',
            'label': 'Ishchi fayllar',
            'path': '/tmp',
            'bytes': 0,
          },
        ],
        'total': 870318080,
        'freed': 0,
      });
      expect(usage.sections, hasLength(2));
      expect(usage.sections.first.label, 'Yuklab olingan videolar');
      expect(usage.sections.first.bytes, 870318080);
      expect(usage.total, 870318080);
    });

    test('survives a malformed payload instead of throwing', () {
      final usage = CacheUsage.fromJson({'sections': 'nonsense'});
      expect(usage.sections, isEmpty);
      expect(usage.total, 0);
      expect(usage.freed, 0);
    });

    test('formats bytes the way the settings screen shows them', () {
      expect(CacheUsage.format(870318080), '830 MB');
      expect(CacheUsage.format(5 * 1024 * 1024 * 1024), '5.0 GB');
      expect(CacheUsage.format(0), '0 MB');
    });
  });

  group('editor draft persistence', () {
    SubtitleSegment segment(String original, String translated) =>
        SubtitleSegment(
          start: 1,
          end: 2,
          original: original,
          translated: translated,
        );

    test('atomically saves, restores and discards matching draft', () async {
      final root = await Directory.systemTemp.createTemp('subtitr-draft-test-');
      addTearDown(() => root.delete(recursive: true));
      final session = File('${root.path}${Platform.pathSeparator}session.json');
      await session.writeAsString('{}');
      final service = DesktopProcessorService();

      await service.saveDraft(
        sessionPath: session.path,
        segments: [segment('asl', 'tahrir')],
      );
      final draftFile = File('${session.path}.draft.json');
      expect(await draftFile.exists(), isTrue);
      expect(jsonDecode(await draftFile.readAsString())['version'], 1);
      final restored = await service.loadDraft(
        sessionPath: session.path,
        expectedSegments: 1,
      );
      expect(restored!.single.translated, 'tahrir');

      await service.discardDraft(session.path);
      expect(await draftFile.exists(), isFalse);
    });

    test('ignores malformed drafts', () async {
      final root = await Directory.systemTemp.createTemp('subtitr-draft-test-');
      addTearDown(() => root.delete(recursive: true));
      final session = File('${root.path}${Platform.pathSeparator}session.json');
      await session.writeAsString('{}');
      await File('${session.path}.draft.json').writeAsString('{not json');
      final service = DesktopProcessorService();
      expect(
        await service.loadDraft(sessionPath: session.path, expectedSegments: 1),
        isNull,
      );
    });
  });

  group('process boundary', () {
    test(
      'forwards streamed progress and cancellation to a fake transport',
      () async {
        final transport = _FakeTransport(
          response: {'type': 'done', 'outputs': []},
        );
        final service = DesktopProcessorService(transport: transport);
        final received = <ProcessorProgress>[];

        await service.installDependencies(onProgress: received.add);
        await service.cancel();

        expect(transport.streamedArguments, ['install-deps']);
        expect(received.single.message, 'Ishlanmoqda');
        expect(received.single.progress, 0.5);
        expect(transport.cancelled, isTrue);
      },
    );

    test('parses noisy JSON output and surfaces processor errors', () {
      expect(
        parseProcessorJsonOutput(
          stdout: '''starting
{"type":"done","value":7}
''',
          stderr: '',
          exitCode: 0,
          arguments: const ['scan'],
        )['value'],
        7,
      );
      expect(
        () => parseProcessorJsonOutput(
          stdout: '{"type":"error","message":"xato"}',
          stderr: '',
          exitCode: 1,
          arguments: const ['scan'],
        ),
        throwsA(isA<StateError>()),
      );
    });

    test(
      'session store removes temporary segment data after explicit cleanup',
      () async {
        final directory = await Directory.systemTemp.createTemp(
          'subtitr-store-test-',
        );
        addTearDown(() => directory.delete(recursive: true));
        final store = ProcessorSessionStore(temporaryDirectory: directory);
        final temporary = await store.writeSegments('edits_', [
          {'original': 'asl', 'translated': 'tarjima'},
        ]);
        expect(await temporary.exists(), isTrue);
        await store.deleteQuietly(temporary);
        expect(await temporary.exists(), isFalse);
      },
    );
  });
}
