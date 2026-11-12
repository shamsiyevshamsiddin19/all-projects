import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/widgets/history_panel.dart';

void main() {
  testWidgets('HistoryPanel renders empty state when no items', (tester) async {
    var closed = false;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: HistoryPanel(
            items: const [],
            onClose: () => closed = true,
            onPlay: (_) {},
            onOpenFolder: (_) {},
            onOpenOutputFolder: () {},
            onRefresh: () {},
          ),
        ),
      ),
    );

    expect(find.text('Jarayonlar tarixi'), findsOneWidget);
    expect(find.text("Hali yakunlangan natijalar yo'q"), findsOneWidget);

    await tester.tap(find.byTooltip('Yopish'));
    await tester.pump();
    expect(closed, isTrue);
  });

  testWidgets('HistoryPanel renders items and triggers play and open folder callbacks', (tester) async {
    String? playedVideo;
    String? openedFolder;

    final items = [
      HistoryEntry(
        name: 'Rihanna Diamonds',
        directoryPath: '/videos/rihanna',
        videoPath: '/videos/rihanna/diamonds.mp4',
        subtitlePath: '/videos/rihanna/diamonds.srt',
        modified: DateTime(2026, 11, 6, 21, 45),
      ),
      HistoryEntry(
        name: 'Hobbit Trailer',
        directoryPath: '/videos/hobbit',
        videoPath: null,
        subtitlePath: '/videos/hobbit/hobbit.ass',
        modified: DateTime(2026, 11, 5, 14, 30),
      ),
    ];

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: HistoryPanel(
            items: items,
            onClose: () {},
            onPlay: (p) => playedVideo = p,
            onOpenFolder: (p) => openedFolder = p,
            onOpenOutputFolder: () {},
            onRefresh: () {},
          ),
        ),
      ),
    );

    expect(find.text('Rihanna Diamonds'), findsOneWidget);
    expect(find.text('Hobbit Trailer'), findsOneWidget);
    expect(find.text('VIDEO'), findsOneWidget);
    expect(find.text('SRT'), findsOneWidget);
    expect(find.text('ASS'), findsOneWidget);

    // Play tugmasi bosilishi
    await tester.tap(find.byTooltip("Ilova pleyerida ko'rish"));
    await tester.pump();
    expect(playedVideo, '/videos/rihanna/diamonds.mp4');

    // Papkani ochish bosilishi (2 ta folder iconi bor)
    await tester.tap(find.byTooltip('Papkani ochish').first);
    await tester.pump();
    expect(openedFolder, '/videos/rihanna');
  });
}
