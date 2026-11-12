import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/widgets/home_screen_chrome.dart';

void main() {
  testWidgets('HomeScreenAppBar renders history button and triggers callback', (tester) async {
    var historyTapped = false;
    var keysTapped = false;
    var notificationsTapped = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          appBar: HomeScreenAppBar(
            appVersion: '1.2.0',
            hasApiKey: true,
            configuredProviders: const ['groq', 'openai'],
            isRunning: false,
            unreadNotificationCount: 2,
            canOpenOutput: true,
            onShowHistory: () => historyTapped = true,
            onOpenApiKeys: () => keysTapped = true,
            onInstallDependencies: () {},
            onShowNotifications: () => notificationsTapped = true,
            onOpenOutput: () {},
          ),
        ),
      ),
    );

    // Tarix tugmasi ko'rinishi va tooltip tekshiruvi
    expect(find.byIcon(Icons.history_rounded), findsOneWidget);
    expect(find.byTooltip('Tarix'), findsOneWidget);

    // Boshqa tugmalar bilan bir qatorda mavjudligi
    expect(find.byIcon(Icons.key_rounded), findsOneWidget);
    expect(find.byIcon(Icons.download_for_offline_rounded), findsOneWidget);
    expect(find.byIcon(Icons.notifications_none_rounded), findsOneWidget);
    expect(find.byIcon(Icons.output_rounded), findsOneWidget);

    // Tarix tugmasi bosilishi
    await tester.tap(find.byIcon(Icons.history_rounded));
    await tester.pump();
    expect(historyTapped, isTrue);

    // Kalit tugmasi bosilishi
    await tester.tap(find.byIcon(Icons.key_rounded));
    await tester.pump();
    expect(keysTapped, isTrue);
  });
}
