import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:subtitr_app/screens/translation_editor_screen.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';

/// The editor flags the lines the model was unsure of. Those are where a
/// misheard name or wrong word tends to be, so the user does not have to
/// read every line looking for them.
/// Records what the editor asks for instead of running the processor.
class _FakeProcessor extends DesktopProcessorService {
  _FakeProcessor(this.imagePath);

  final String imagePath;
  final List<double> askedAt = [];
  String? appearanceMode;

  /// Widget testida haqiqiy jarayon ishga tushmasligi uchun: pleyer
  /// yo'li darhol tushadi va tahrirlash oynasi kadr ko'rishga qaytadi.
  @override
  Future<({String subtitles, String video})> subtitleFile({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required String mode,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
    String origStyle = 'box',
  }) async {
    throw StateError('test: pleyer ishlatilmaydi');
  }

  @override
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
    askedAt.add(at);
    appearanceMode = mode;
    return imagePath;
  }
}

void main() {
  SubtitleSegment line(double start, String original, double? confidence) =>
      SubtitleSegment(
        start: start,
        end: start + 2,
        original: original,
        translated: 'tarjima',
        confidence: confidence,
      );

  PreparedSession sessionWith(List<SubtitleSegment> segments) => PreparedSession(
        sessionPath: '/tmp/s.json',
        video: '/tmp/v.mp4',
        mode: 'dual',
        sourceLang: 'ru',
        targetLang: 'uz',
        transcriber: 'groq',
        translator: 'claude',
        segments: segments,
        vocabCount: 0,
      );

  Future<void> open(
    WidgetTester tester,
    List<SubtitleSegment> segments, {
    DesktopProcessorService? service,
    Size size = const Size(700, 900),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    await tester.pumpWidget(MaterialApp(
      home: TranslationEditorScreen(
        session: sessionWith(segments),
        service: service,
      ),
    ));
    await tester.pumpAndSettle();
  }

  test('a missing score is not treated as uncertain', () {
    expect(line(0, 'tayyor srt', null).isUncertain, isFalse);
    expect(line(0, 'ishonchli', 0.9).isUncertain, isFalse);
    expect(line(0, 'shubhali', 0.2).isUncertain, isTrue);
  });

  test('confidence survives a JSON round trip', () {
    final parsed = SubtitleSegment.fromJson(line(1, 'matn', 0.31).toJson());
    expect(parsed.confidence, closeTo(0.31, 1e-9));
    expect(parsed.isUncertain, isTrue);
  });

  test('an unknown score is omitted from JSON rather than sent as zero', () {
    expect(line(1, 'matn', null).toJson().containsKey('confidence'), isFalse);
  });

  testWidgets('uncertain lines are marked and counted', (tester) async {
    await open(tester, [
      line(0, 'ishonchli qator', 0.95),
      line(2, 'shubhali qator', 0.18),
      line(4, 'yana shubhali', 0.30),
    ]);
    expect(find.text('tekshiring'), findsNWidgets(2));
    expect(find.text('Shubhali 2'), findsOneWidget);
  });

  testWidgets('no chip when every line is confident', (tester) async {
    await open(tester, [line(0, 'bir', 0.9), line(2, 'ikki', 0.8)]);
    expect(find.text('tekshiring'), findsNothing);
    expect(find.textContaining('Shubhali'), findsNothing);
  });

  testWidgets('an edit survives the row scrolling out of view', (tester) async {
    // Ilgari har qator uchun kontroller oldindan yaratilardi (2 soatlik
    // kinoda ~2000 ta). Endi kontroller qator ko'ringandagina yashaydi,
    // shuning uchun tahrir SEGMENTGA yozilishi shart — aks holda
    // ro'yxatni aylantirganda yo'qoladi.
    final segments = [
      for (var i = 0; i < 40; i++) line(i * 3.0, 'qator $i', null),
    ];
    await open(tester, segments, size: const Size(700, 500));

    await tester.enterText(find.byType(TextField).at(1), 'MENING TARJIMAM');
    await tester.pump();
    expect(segments[0].translated, 'MENING TARJIMAM');

    // Juda pastga aylantiramiz — birinchi qator butunlay yo'qoladi.
    await tester.drag(find.byType(ListView), const Offset(0, -4000));
    await tester.pumpAndSettle();
    expect(find.text('qator 0'), findsNothing, reason: 'qator hali ekranda');

    // Orqaga qaytamiz — matn joyida bo'lishi kerak.
    await tester.drag(find.byType(ListView), const Offset(0, 4000));
    await tester.pumpAndSettle();
    expect(segments[0].translated, 'MENING TARJIMAM');
    expect(find.text('MENING TARJIMAM'), findsOneWidget);
  });

  testWidgets('only visible rows hold a controller', (tester) async {
    final segments = [
      for (var i = 0; i < 300; i++) line(i * 3.0, 'qator $i', null),
    ];
    await open(tester, segments, size: const Size(700, 500));
    // 300 qator, lekin ekranda o'nga yaqini. Ilgari 300 ta kontroller
    // bir vaqtda yashardi.
    final fields = tester.widgetList(find.byType(TextField)).length;
    expect(fields, lessThan(30),
        reason: '$fields ta maydon qurildi — kontrollerlar hali oldindan yaratilyapti');
  });

  testWidgets('tapping preview asks for the middle of the line', (tester) async {
    final png = File('${Directory.systemTemp.path}/subtitr_test_frame.png')
      ..writeAsBytesSync(_onePixelPng);
    addTearDown(() {
      if (png.existsSync()) png.deleteSync();
    });
    final fake = _FakeProcessor(png.path);
    // Keng oyna — kadr paneli yonma-yon chiqadi.
    await open(tester, [line(10, 'birinchi', null)],
        service: fake, size: const Size(1300, 900));

    await tester.tap(find.byIcon(Icons.image_outlined).first);
    await tester.pumpAndSettle();

    // Bo'lak 10..12 — o'rtasi 11. Boshida oldingi subtitr hali turgan
    // bo'lishi mumkin, shuning uchun o'rtasi olinadi.
    expect(fake.askedAt, [11.0]);
    expect(fake.appearanceMode, 'dual');
  });

  testWidgets('the preview panel only appears in a wide window', (tester) async {
    await open(tester, [line(0, 'bir', null)], size: const Size(700, 900));
    expect(find.textContaining('shu yerda ko'), findsNothing);

    await open(tester, [line(0, 'bir', null)], size: const Size(1300, 900));
    expect(find.textContaining('shu yerda ko'), findsOneWidget);
  });

  testWidgets('the filter narrows the list to uncertain lines', (tester) async {
    await open(tester, [
      line(0, 'ishonchli qator', 0.95),
      line(2, 'shubhali qator', 0.18),
    ]);
    expect(find.text('ishonchli qator'), findsOneWidget);

    await tester.tap(find.text('Shubhali 1'));
    await tester.pumpAndSettle();

    expect(find.text('shubhali qator'), findsOneWidget);
    expect(find.text('ishonchli qator'), findsNothing);
  });
}


/// Smallest valid PNG — Image.file needs real bytes, not an empty file.
final _onePixelPng = <int>[
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
  0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
  0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
  0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
  0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
];
