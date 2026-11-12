import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/models/studio_media_file.dart';
import 'package:subtitr_app/widgets/document_viewer.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Directory tempDir;
  late File textFile;
  late File mdFile;
  late File srtFile;

  setUp(() {
    tempDir = Directory.systemTemp.createTempSync('studio_doc_test_');
    textFile = File('${tempDir.path}/test_doc.txt')
      ..writeAsStringSync('Salom dunyo!\nBu test hujjati.\nIkkinchi qator.');
    mdFile = File('${tempDir.path}/notes_oqish.md')
      ..writeAsStringSync('# Sarlavha\n\n- Birinchi band\n- Ikkinchi band :: tarjimasi');
    srtFile = File('${tempDir.path}/subtitles.srt')
      ..writeAsStringSync('1\n00:00:01,000 --> 00:00:03,000\nHello World\n');
  });

  tearDown(() {
    try {
      tempDir.deleteSync(recursive: true);
    } catch (_) {}
  });

  testWidgets('DocumentViewer loads text file and displays content and stats', (tester) async {
    bool closed = false;

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: DocumentViewer(
            filePath: textFile.path,
            title: 'Test Text File',
            onClose: () => closed = true,
          ),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('Test Text File'), findsOneWidget);
    expect(find.text('TXT'), findsOneWidget);
    expect(find.textContaining('Salom dunyo!'), findsOneWidget);
    expect(find.textContaining('3 qator'), findsOneWidget);

    // Test close button
    await tester.tap(find.byTooltip('Yopish'));
    await tester.pump();
    expect(closed, isTrue);
  });

  testWidgets('DocumentViewer search filters text lines', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: DocumentViewer(
            filePath: textFile.path,
            onClose: () {},
          ),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    // Enter search query
    await tester.enterText(find.byType(TextField), 'Ikkinchi');
    await tester.pump();

    expect(find.textContaining('Ikkinchi qator.'), findsOneWidget);
    // Salom dunyo shouldn't match
    expect(find.textContaining('Salom dunyo!'), findsNothing);
  });

  testWidgets('DocumentViewer handles markdown and font size zooming', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: DocumentViewer(
            filePath: mdFile.path,
            onClose: () {},
          ),
        ),
      ),
    );

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('MD'), findsOneWidget);
    expect(find.textContaining('Birinchi band'), findsOneWidget);

    // Zoom in
    await tester.tap(find.byTooltip("Shriftni kattalashtirish (A+)"));
    await tester.pump();

    // Zoom out
    await tester.tap(find.byTooltip("Shriftni kichiklashtirish (A-)"));
    await tester.pump();
  });

  test('StudioMediaFile categorization and discovery works correctly', () {
    expect(StudioMediaFile.categorize('video.mp4'), equals(StudioFileCategory.video));
    expect(StudioMediaFile.categorize('sample.pdf'), equals(StudioFileCategory.pdf));
    expect(StudioMediaFile.categorize('doc.docx'), equals(StudioFileCategory.docx));
    expect(StudioMediaFile.categorize('notes.md'), equals(StudioFileCategory.markdown));
    expect(StudioMediaFile.categorize('subs.srt'), equals(StudioFileCategory.subtitle));
    expect(StudioMediaFile.categorize('subs.ass'), equals(StudioFileCategory.subtitle));

    expect(StudioMediaFile.isSupported('movie.mkv'), isTrue);
    expect(StudioMediaFile.isSupported('notes.pdf'), isTrue);
    expect(StudioMediaFile.isSupported('image.png'), isFalse);

    final discovered = StudioMediaFile.discover(textFile.path);
    expect(discovered.length, greaterThanOrEqualTo(3));
  });
}
