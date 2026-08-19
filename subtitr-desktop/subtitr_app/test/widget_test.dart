// Basic smoke test for the Subtitr Desktop app.
//
// The app is launched with autoScan disabled so it does not try to spawn the
// Python processor during the test. We simply verify the shell renders.

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:subtitr_app/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    // Provide an in-memory store so SettingsStore.load() works under test.
    SharedPreferences.setMockInitialValues(<String, Object>{});
  });

  testWidgets('App renders the main shell', (WidgetTester tester) async {
    // Desktop app — render at a realistic desktop window size (wide layout).
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(const SubtitleApp(autoScan: false));
    await tester.pump();

    // App title is shown in the AppBar.
    expect(find.text('Subtitr Desktop'), findsOneWidget);
    // The primary action button is present.
    expect(find.text('Boshlash'), findsOneWidget);
  });
}
