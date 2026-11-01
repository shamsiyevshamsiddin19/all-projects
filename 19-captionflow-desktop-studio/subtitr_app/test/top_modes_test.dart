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
    ValueChanged<String>? onModeChanged,
    ValueChanged<String>? onVoiceChanged,
    ValueChanged<double>? onDuckingChanged,
  }) {
    return MaterialApp(
      home: Scaffold(
        body: SizedBox(
          width: 500,
          height: 800,
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
            onAppearanceChanged: (_) {},
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

    // 3 ta asosiy tugma matnlari
    expect(find.text('Kuydirish'), findsOneWidget);
    expect(find.text('Yumshoq'), findsOneWidget);
    expect(find.text('AI Dublyaj'), findsOneWidget);
  });

  testWidgets('Yumshoq subtitr tanlanganda 2 subtitr izohi chiqadi', (tester) async {
    String? selectedMode;
    await tester.pumpWidget(
      harness(
        mode: 'dual_vocab',
        onModeChanged: (v) => selectedMode = v,
      ),
    );
    await tester.pumpAndSettle();

    // Yumshoq tugmasini bosamiz
    await tester.tap(find.text('Yumshoq'));
    await tester.pumpAndSettle();

    expect(selectedMode, 'softsub');

    // Endi softsub holatida ekranni ko'ramiz
    await tester.pumpWidget(harness(mode: 'softsub'));
    await tester.pumpAndSettle();

    expect(find.textContaining('2 ta subtitr (Original + Tarjima)'), findsOneWidget);
  });

  testWidgets('AI Dublyaj tanlanganda ovoz va ducking sozlamalari ko\'rinadi', (tester) async {
    String? selectedVoice;

    await tester.pumpWidget(
      harness(
        mode: 'dubbing',
        voice: 'uz-UZ-SardorNeural',
        onVoiceChanged: (v) => selectedVoice = v,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Sardor'), findsOneWidget);
    expect(find.text('Madina'), findsOneWidget);
    expect(find.text('Asl fon ovozi balandligi (Ducking)'), findsOneWidget);

    // Madina ovozini tanlaymiz
    await tester.tap(find.text('Madina'));
    await tester.pumpAndSettle();

    expect(selectedVoice, 'uz-UZ-MadinaNeural');
  });
}
