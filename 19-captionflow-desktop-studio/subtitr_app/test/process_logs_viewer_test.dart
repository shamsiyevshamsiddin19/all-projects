import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/widgets/process_logs_viewer.dart';
import 'package:subtitr_app/widgets/processing_panel.dart';

void main() {
  testWidgets('ProcessLogsConsole renders empty state, live logs and percentage badges', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final logs = [
      ProcessLogEntry(
        timestamp: DateTime(2026, 11, 12, 12, 34, 56),
        message: 'Audio ajratilmoqda',
        progress: 0.18,
      ),
      ProcessLogEntry(
        timestamp: DateTime(2026, 11, 12, 12, 35, 10),
        message: 'Whisper transkripsiya boshlandi',
        progress: 0.30,
        level: ProcessLogLevel.info,
      ),
      ProcessLogEntry(
        timestamp: DateTime(2026, 11, 12, 12, 36, 0),
        message: 'Muvaffaqiyatli yakunlandi',
        progress: 1.0,
        level: ProcessLogLevel.success,
      ),
    ];

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: ProcessLogsConsole(
            liveLogs: logs,
            isRunning: true,
            embedded: true,
          ),
        ),
      ),
    );

    await tester.pump();

    // Check title and counter
    expect(find.text('Jarayon loglari'), findsOneWidget);
    expect(find.text('JONLI'), findsOneWidget);
    expect(find.text('3 ta satr'), findsOneWidget);

    // Check log entries
    expect(find.text('[12:34:56]'), findsOneWidget);
    expect(find.text('18%'), findsOneWidget);
    expect(find.text('Audio ajratilmoqda'), findsOneWidget);

    expect(find.text('[12:35:10]'), findsOneWidget);
    expect(find.text('30%'), findsOneWidget);
    expect(find.text('Whisper transkripsiya boshlandi'), findsOneWidget);

    expect(find.text('Muvaffaqiyatli yakunlandi'), findsOneWidget);
  });

  testWidgets('ProcessLogsConsole filter works and disk logs tab loads content', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    final logs = [
      ProcessLogEntry(
        timestamp: DateTime(2026, 11, 12, 10, 0, 0),
        message: 'FFmpeg boshlandi',
      ),
      ProcessLogEntry(
        timestamp: DateTime(2026, 11, 12, 10, 0, 5),
        message: 'Groq API so\'rovi',
      ),
    ];

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: ProcessLogsConsole(
            liveLogs: logs,
            onLoadDiskLogs: () async => '2026-11-12 10:00:00 INFO --- buyruq: process ---\n2026-11-12 10:00:01 INFO Tayyor',
            embedded: true,
          ),
        ),
      ),
    );

    await tester.pump();

    // Filter test
    await tester.enterText(find.byType(TextField), 'Groq');
    await tester.pump();

    expect(find.text('Groq API so\'rovi'), findsOneWidget);
    expect(find.text('FFmpeg boshlandi'), findsNothing);

    // Clear filter
    await tester.enterText(find.byType(TextField), '');
    await tester.pump();
    expect(find.text('FFmpeg boshlandi'), findsOneWidget);

    // Switch to Disk logs tab
    await tester.tap(find.text('Tizim fayli'));
    await tester.pumpAndSettle();

    expect(find.textContaining('--- buyruq: process ---'), findsOneWidget);
  });

  testWidgets('ProcessingPanel renders Loglar button and toggles embedded console', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    bool logsVisible = false;

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: StatefulBuilder(
          builder: (context, setState) {
            return Scaffold(
              body: ProcessingPanel(
                selectedName: 'movie.mp4',
                selectedPath: '/videos/movie.mp4',
                outDir: '/out',
                isRunning: true,
                progress: 0.18,
                status: 'Audio ajratilmoqda',
                result: null,
                onStart: () {},
                onOpenPath: (_) async {},
                isLogsVisible: logsVisible,
                onToggleLogs: () => setState(() => logsVisible = !logsVisible),
                liveLogs: [
                  ProcessLogEntry(
                    timestamp: DateTime.now(),
                    message: 'Audio ajratilmoqda',
                    progress: 0.18,
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );

    await tester.pump();

    // Verify 'Loglar' button exists in buttons row
    expect(find.text('Loglar'), findsOneWidget);
    expect(find.byIcon(Icons.terminal_outlined), findsOneWidget);

    // Console not visible initially
    expect(find.text('3 ta satr'), findsNothing);

    // Tap 'Loglar' button
    await tester.tap(find.text('Loglar'));
    await tester.pump();

    expect(logsVisible, isTrue);
    expect(find.text('Loglarni yashirish'), findsOneWidget);
    expect(find.text('Jarayon loglari'), findsOneWidget);
    expect(find.text('1 ta satr'), findsOneWidget);

    // Tap to hide
    await tester.tap(find.text('Loglarni yashirish'));
    await tester.pump();

    expect(logsVisible, isFalse);
    expect(find.text('Loglar'), findsOneWidget);
  });
}
