import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/services/settings_store.dart';
import 'package:subtitr_app/widgets/settings_panel.dart';

/// "O'qish uchun matn" rejimi namunasi A4 nisbatli sahifa chizadi — tor
/// panelda ham toshib ketmasligi kerak.
void main() {
  const modes = [
    ModeChoice(
      value: 'reading',
      icon: Icons.auto_stories_rounded,
      title: 'O\'qish uchun matn',
      description: 'Videoni qayta ko\'rmasdan o\'qish uchun PDF va TXT',
    ),
    ModeChoice(
      value: 'dual_vocab',
      icon: Icons.view_sidebar_rounded,
      title: 'Tarjima + lug\'at',
      description: 'Pastda original va tarjima',
    ),
    ModeChoice(
      value: 'translated',
      icon: Icons.translate_rounded,
      title: 'Faqat tarjima',
      description: 'Videoda faqat tarjima subtitri ko\'rinadi',
    ),
  ];

  Widget harness(String mode, Size size) => MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: size.width,
            height: size.height,
            child: SettingsPanel(
              modes: modes,
              mode: mode,
              sourceLang: 'ru',
              targetLang: 'uz',
              appearance: const AppearanceSettings(),
              isRunning: false,
              onModeChanged: (_) {},
              onSourceLangChanged: (_) {},
              onTargetLangChanged: (_) {},
              onAppearanceChanged: (_) {},
            ),
          ),
        ),
      );

  // Oyna kichraytirilganda ham hech narsa chetidan toshmasligi kerak:
  // ilova oynasining eng kichik o'lchami cheklanmagan.
  for (final size in const [
    Size(600, 760),
    Size(560, 520),
    Size(640, 400),
    Size(420, 760),
    Size(320, 560),
  ]) {
    testWidgets('reading namunasi ${size.width}x${size.height} da toshmaydi',
        (tester) async {
      tester.view.physicalSize = size * 2;
      tester.view.devicePixelRatio = 2.0;
      addTearDown(tester.view.reset);

      await tester.pumpWidget(harness('reading', size));
      await tester.pumpAndSettle();

      expect(tester.takeException(), isNull);
      expect(find.byType(SettingsPanel), findsOneWidget);
    });
  }

  // "Faqat tarjima" da ko'rinish sozlamalaridan bittasi ("Asl matn")
  // yashiriladi — qolgan qatorning maketi buzilmasligi kerak.
  testWidgets('faqat tarjima rejimi namunasi va sozlamalari', (tester) async {
    tester.view.physicalSize = const Size(600, 760) * 2;
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(harness('translated', const Size(600, 760)));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    // Asl matn uslubi ko'rsatilmaydi, tarjima rangi esa qoladi.
    expect(find.text('Asl matn'), findsNothing);
    expect(find.text('Rang'), findsOneWidget);
  });

  testWidgets('video rejimida "Asl matn" sozlamasi bor', (tester) async {
    tester.view.physicalSize = const Size(600, 760) * 2;
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(harness('dual_vocab', const Size(600, 760)));
    await tester.pumpAndSettle();
    expect(find.text('Asl matn'), findsOneWidget);
  });

  testWidgets('video rejimi namunasi hamon ishlaydi', (tester) async {
    tester.view.physicalSize = const Size(600, 760) * 2;
    tester.view.devicePixelRatio = 2.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(harness('dual_vocab', const Size(600, 760)));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}
