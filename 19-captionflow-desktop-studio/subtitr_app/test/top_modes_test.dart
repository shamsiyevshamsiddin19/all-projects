import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/services/settings_store.dart';
import 'package:subtitr_app/widgets/settings_panel.dart';

void main() {



  const modes = [
    ModeChoice(
      value: 'dual_vocab',
      icon: Icons.view_sidebar_rounded,
      title: 'Tarjima + lug\'at',
      description: 'Pastda original va tarjima, chapda so\'zlar',
    ),
    ModeChoice(
      value: 'dual',
      icon: Icons.layers_rounded,
      title: 'Ikki qator subtitr',
      description: 'Original va tarjima pastda',
    ),
    ModeChoice(
      value: 'softsub',
      icon: Icons.closed_caption_rounded,
      title: 'Yumshoq subtitr (CC)',
      description: 'Kuydirmasdan, 2 ta subtitr qo\'shish',
    ),
    ModeChoice(
      value: 'dubbing',
      icon: Icons.record_voice_over_rounded,
      title: 'AI Dublyaj',
      description: 'O\'zbekcha AI ovoz, asl musiqa saqlanadi',
    ),
  ];

  Widget harness({
    required String mode,
    String voice = 'uz-UZ-SardorNeural',
    double ducking = 0.18,
    Size size = const Size(500, 800),
    ValueChanged<String>? onModeChanged,
    ValueChanged<String>? onVoiceChanged,
    ValueChanged<double>? onDuckingChanged,
    ValueChanged<AppearanceSettings>? onAppearanceChanged,
  }) {
    return MaterialApp(
      home: Scaffold(
        body: SizedBox(
          width: size.width,
          height: size.height,
          child: SettingsPanel(
            modes: modes,
            mode: mode,
            sourceLang: 'en',
            targetLang: 'uz',
            appearance: const AppearanceSettings(),
            voice: voice,
            ducking: ducking,
            isRunning: false,
            onModeChanged: onModeChanged ?? (_) {},
            onSourceLangChanged: (_) {},
            onTargetLangChanged: (_) {},
            onAppearanceChanged: onAppearanceChanged ?? (_) {},
            onVoiceChanged: onVoiceChanged ?? (_) {},
            onDuckingChanged: onDuckingChanged ?? (_) {},
          ),
        ),
      ),
    );
  }

  


  testWidgets('Eng tepada 3 ta rejim tugmasi mavjud', (tester) async {
    await tester.pumpWidget(harness(mode: 'dual_vocab'));
    await tester.pumpAndSettle();

    expect(find.text('Kuydirish'), findsOneWidget);
    expect(find.text('Yumshoq'), findsOneWidget);
    expect(find.text('AI Dublyaj'), findsOneWidget);
  });

  testWidgets('Kuydirish tugmasi bosilganda dual_vocab tanlanadi', (tester) async {
    String? selectedMode;
    await tester.pumpWidget(
      harness(
        mode: 'softsub',
        onModeChanged: (v) => selectedMode = v,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Kuydirish'));
    await tester.pumpAndSettle();

    expect(selectedMode, 'dual_vocab');
  });

  testWidgets('Yumshoq subtitr tanlanganda uslub tanlash va preview ko\'rinadi', (tester) async {
    String? selectedMode;
    await tester.pumpWidget(
      harness(
        mode: 'dual_vocab',
        onModeChanged: (v) => selectedMode = v,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Yumshoq'));
    await tester.pumpAndSettle();

    expect(selectedMode, 'softsub');

    await tester.pumpWidget(harness(mode: 'softsub'));
    await tester.pumpAndSettle();

    expect(find.text('Yumshoq subtitr uslubi'), findsOneWidget);
    expect(find.text('CC: 2 ta alohida trek'), findsOneWidget);
  });

  testWidgets('AI Dublyaj tanlanganda ovoz va ducking sozlamalari ko\'rinadi', (tester) async {
    String? selectedVoice;

    await tester.pumpWidget(
      harness(
        mode: 'dubbing',
        voice: 'uz-UZ-SardorNeural',
        ducking: 0.18,
        onVoiceChanged: (v) => selectedVoice = v,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Sardor'), findsOneWidget);
    expect(find.text('Madina'), findsOneWidget);
    expect(find.text('Asl fon ovozi balandligi (Ducking)'), findsOneWidget);
    expect(find.text('Multi-Audio: 2 trek'), findsOneWidget);

    // Madina ovozini tanlaymiz
    await tester.tap(find.text('Madina'));
    await tester.pumpAndSettle();
    expect(selectedVoice, 'uz-UZ-MadinaNeural');

    // Sardor ovozini tanlaymiz
    await tester.tap(find.text('Sardor'));
    await tester.pumpAndSettle();
    expect(selectedVoice, 'uz-UZ-SardorNeural');
  });

  testWidgets('Ducking qiymatini o\'zgartirish ishlaydi', (tester) async {
    double? selectedDucking;

    await tester.pumpWidget(
      harness(
        mode: 'dubbing',
        onDuckingChanged: (v) => selectedDucking = v,
      ),
    );
    await tester.pumpAndSettle();

    // Ducking dropdown'ni ochamiz
    await tester.tap(find.text('18% — Tavsiya (Musiqa va effektlar eshitiladi)'));
    await tester.pumpAndSettle();

    // 10% tanlaymiz
    await tester.tap(find.text('10% — Past fon (AI ovoz yanada aniq)').last);
    await tester.pumpAndSettle();

    expect(selectedDucking, 0.10);
  });

  testWidgets('Ketma-ket rejimlar almashganda xatolik yuz bermaydi', (tester) async {
    var currentMode = 'dual_vocab';
    await tester.pumpWidget(
      StatefulBuilder(
        builder: (context, setState) {
          return harness(
            mode: currentMode,
            onModeChanged: (v) => setState(() => currentMode = v),
          );
        },
      ),
    );
    await tester.pumpAndSettle();

    // Softsub ga o'tish
    await tester.tap(find.text('Yumshoq'));
    await tester.pumpAndSettle();
    expect(currentMode, 'softsub');

    // Dublyajga o'tish
    await tester.tap(find.text('AI Dublyaj'));
    await tester.pumpAndSettle();
    expect(currentMode, 'dubbing');

    // Kuydirishga qaytish
    await tester.tap(find.text('Kuydirish'));
    await tester.pumpAndSettle();
    expect(currentMode, 'dual_vocab');
  });

  for (final size in const [
    Size(440, 750),
    Size(400, 680),
    Size(360, 550),
  ]) {
    testWidgets('Kichik ekran $size da toshib ketmaydi', (tester) async {
      tester.view.physicalSize = size * 2;
      tester.view.devicePixelRatio = 2.0;
      addTearDown(tester.view.reset);
      await tester.pumpWidget(harness(mode: 'dubbing', size: size));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    });
  }
}
