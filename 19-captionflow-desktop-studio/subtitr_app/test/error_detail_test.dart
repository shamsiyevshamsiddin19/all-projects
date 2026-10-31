import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:subtitr_app/screens/home_screen.dart';

/// Errors from ffmpeg or a provider are long and put the useful part at the
/// end, but the snackbar cuts off after three lines. These check the full
/// text is reachable and copyable.
void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  const longError = 'Video render xato: ffmpeg oqimni ocha olmadi. '
      'Stream #0:1 -> #0:1 (opus (native) -> aac (native)). '
      'Error while filtering: Invalid argument. '
      'Conversion failed! Bu oxirgi qism — eng muhimi va kesilib ketardi.';

  Future<void> raise(WidgetTester tester) async {
    tester.view.physicalSize = const Size(1400, 1000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);
    // autoScan: false — test protsessor jarayonini ishga tushirmasin.
    await tester.pumpWidget(const MaterialApp(home: HomeScreen(autoScan: false)));
    await tester.pumpAndSettle();

    final state = tester.state(find.byType(HomeScreen));
    // ignore: avoid_dynamic_calls
    (state as dynamic).showErrorForTest(longError);
    await tester.pumpAndSettle();
  }

  testWidgets('the snackbar offers a way to see the whole error',
      (tester) async {
    await raise(tester);
    expect(find.text('Batafsil'), findsOneWidget);
  });

  testWidgets('the detail dialog shows the end of the message too',
      (tester) async {
    await raise(tester);
    await tester.tap(find.text('Batafsil'));
    await tester.pumpAndSettle();

    expect(find.text('Xato tafsiloti'), findsOneWidget);
    final shown = tester.widget<SelectableText>(find.byType(SelectableText));
    expect(shown.data, longError);
    expect(shown.data, contains('eng muhimi va kesilib ketardi'));
  });

  testWidgets('the error can be copied', (tester) async {
    final copied = <String>[];
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        if (call.method == 'Clipboard.setData') {
          copied.add(call.arguments['text'] as String);
        }
        return null;
      },
    );
    addTearDown(() => tester.binding.defaultBinaryMessenger
        .setMockMethodCallHandler(SystemChannels.platform, null));

    await raise(tester);
    await tester.tap(find.text('Batafsil'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Nusxa olish'));
    await tester.pumpAndSettle();

    expect(copied, [longError]);
  });

  testWidgets('the dialog points at the logs, where the traceback is',
      (tester) async {
    await raise(tester);
    await tester.tap(find.text('Batafsil'));
    await tester.pumpAndSettle();
    expect(find.text('Loglarni ochish'), findsOneWidget);
  });
}
