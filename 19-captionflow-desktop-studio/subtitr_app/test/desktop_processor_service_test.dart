import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';

void main() {
  test('DesktopVideo parses scan JSON', () {
    final video = DesktopVideo.fromJson({
      'name': 'movie.mp4',
      'path': r'E:\Subtitle\Kinolar\movie.mp4',
      'size': 1024,
      'subtitleName': 'movie.srt',
    });

    expect(video.name, 'movie.mp4');
    expect(video.size, 1024);
    expect(video.subtitleName, 'movie.srt');
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
          {'name': 'work', 'label': 'Ishchi fayllar', 'path': '/tmp', 'bytes': 0},
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
}
