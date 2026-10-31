import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:subtitr_app/screens/translation_editor_screen.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';

/// The editor flags the lines the model was unsure of. Those are where a
/// misheard name or wrong word tends to be, so the user does not have to
/// read every line looking for them.
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

  Future<void> open(WidgetTester tester, List<SubtitleSegment> segments) async {
    await tester.pumpWidget(MaterialApp(
      home: TranslationEditorScreen(session: sessionWith(segments)),
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
