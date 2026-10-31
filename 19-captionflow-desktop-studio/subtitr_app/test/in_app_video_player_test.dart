import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/widgets/in_app_video_player.dart';
import 'package:subtitr_app/widgets/processing_panel.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('InAppVideoPlayerDialog renders title, badges and actions', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    bool externalOpened = false;

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: InAppVideoPlayerDialog(
            videoPath: '/dummy/movies/sample_movie.mp4',
            title: 'sample_movie.mp4',
            onOpenExternal: () {
              externalOpened = true;
            },
          ),
        ),
      ),
    );

    // Initial pump: renders the chrome header and loading/error view
    await tester.pump();

    expect(find.text('sample_movie.mp4'), findsOneWidget);
    expect(find.byIcon(Icons.close_rounded), findsOneWidget);
    expect(find.byTooltip('Tashqi pleyerda ochish (VLC / mpv)'), findsOneWidget);

    // Tap external open button
    await tester.tap(find.byTooltip('Tashqi pleyerda ochish (VLC / mpv)'));
    await tester.pump();
    expect(externalOpened, isTrue);
  });

  testWidgets('ProcessingPanel Videoni ochish prioritizes generated video output', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    String? openedPath;

    final fakeResult = ProcessorResult(
      outputs: [
        const ProcessorOutput(
          kind: 'ass',
          label: 'dual ASS',
          path: '/out/sample_dual.ass',
          name: 'sample_dual.ass',
        ),
        const ProcessorOutput(
          kind: 'video',
          label: 'dual video',
          path: '/out/sample_dual.mp4',
          name: 'sample_dual.mp4',
        ),
      ],
      transcriber: 'groq',
      translator: 'groq',
      sourceLang: 'en',
      targetLang: 'uz',
      outDir: '/out',
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: ProcessingPanel(
            selectedName: 'sample.mp4',
            selectedPath: '/raw/sample.mp4',
            outDir: '/out',
            isRunning: false,
            progress: 1.0,
            status: 'Yakunlandi',
            result: fakeResult,
            estimatedSeconds: 0,
            estimateText: '',
            startTime: null,
            lastProgressUpdate: null,
            onStart: () {},
            onReview: () {},
            onCancel: () {},
            videoCount: 1,
            onOpenPath: (path) async {
              openedPath = path;
            },
          ),
        ),
      ),
    );

    await tester.pump();

    // Find and tap 'Videoni ochish' button
    final openVideoBtn = find.widgetWithText(OutlinedButton, 'Videoni ochish');
    expect(openVideoBtn, findsOneWidget);
    await tester.tap(openVideoBtn);
    await tester.pump();

    // Must open the finished dual video, not the raw one!
    expect(openedPath, equals('/out/sample_dual.mp4'));

    // Also verify tapping the result output tile triggers onOpenPath
    openedPath = null;
    final videoTile = find.text('dual video');
    expect(videoTile, findsOneWidget);
    await tester.tap(videoTile);
    await tester.pump();

    expect(openedPath, equals('/out/sample_dual.mp4'));
  });
}
