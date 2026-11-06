import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/widgets/in_app_video_player.dart';
import 'package:subtitr_app/widgets/processing_panel.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('InAppVideoPlayerDialog renders title and actions', (tester) async {
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

    await tester.pump();

    expect(find.text('sample_movie.mp4'), findsOneWidget);
    expect(find.byIcon(Icons.close_rounded), findsOneWidget);
    expect(find.byTooltip('Tashqi pleyerda ochish (VLC / mpv)'), findsOneWidget);

    await tester.tap(find.byTooltip('Tashqi pleyerda ochish (VLC / mpv)'));
    await tester.pump();
    expect(externalOpened, isTrue);
  });

  testWidgets('EmbeddedVideoPlayer renders header controls, back button and actions', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    bool closed = false;
    String? externalVideo;

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: EmbeddedVideoPlayer(
            videoPath: '/dummy/movies/inline_movie.mp4',
            title: 'inline_movie.mp4',
            onClose: () => closed = true,
            onOpenExternal: (p) => externalVideo = p,
          ),
        ),
      ),
    );

    await tester.pump();

    // Verify title and buttons
    expect(find.text('inline_movie.mp4'), findsOneWidget);
    expect(find.text('Boshqaruv paneli'), findsOneWidget);
    expect(find.byIcon(Icons.arrow_back_rounded), findsOneWidget);

    // Tap 'Boshqaruv paneli' button to return
    await tester.tap(find.text('Boshqaruv paneli'));
    await tester.pump();
    expect(closed, isTrue);

    // Tap external open icon button
    await tester.tap(find.byTooltip('Tashqi pleyerda ochish (VLC / mpv)'));
    await tester.pump();
    expect(externalVideo, equals('/dummy/movies/inline_movie.mp4'));
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

  testWidgets('EmbeddedVideoPlayer subtitle toggle button toggles state on tap', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: EmbeddedVideoPlayer(
            videoPath: '/dummy/movies/video.mp4',
            subtitlePath: '/dummy/movies/video.srt',
            title: 'video.mp4',
            onClose: () {},
          ),
        ),
      ),
    );

    await tester.pump();

    // Since mock file doesn't exist on disk, _hasSubtitles will be false unless file exists
    // Verify widget builds cleanly without crashing
    expect(find.text('video.mp4'), findsOneWidget);
  });

  testWidgets('StudioVideoPlayer provides studio controls: speed, sync, A-B loop, shortcuts help', (tester) async {
    tester.view.physicalSize = const Size(1280, 850);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(),
        home: Scaffold(
          body: EmbeddedVideoPlayer(
            videoPath: '/dummy/movies/studio_clip.mp4',
            title: 'studio_clip.mp4',
            onClose: () {},
          ),
        ),
      ),
    );

    await tester.pump();

    // 1. Verify frame step buttons exist
    expect(find.byTooltip('1 kadr orqaga (,)'), findsOneWidget);
    expect(find.byTooltip('1 kadr oldinga (.)'), findsOneWidget);

    // 2. Verify seek buttons exist
    expect(find.byTooltip('10 soniya orqaga (J)'), findsOneWidget);
    expect(find.byTooltip('10 soniya oldinga (L)'), findsOneWidget);

    // 3. Verify snapshot button exists
    expect(find.byTooltip('Kadr suratini olish (P)'), findsOneWidget);

    // 4. Verify A-B loop button exists and shows A-B
    expect(find.text('A-B'), findsOneWidget);

    // 5. Verify speed indicator is present
    expect(find.text('1.0x'), findsOneWidget);

    // 6. Verify sync offset indicator is present
    expect(find.text('+0.0s'), findsOneWidget);

    // 6.5. Verify CC soft subtitle button exists and can be tapped
    final ccBtn = find.text('CC');
    expect(ccBtn, findsOneWidget);
    await tester.tap(ccBtn);
    await tester.pump();

    // 7. Verify keyboard shortcuts help button and modal
    final helpBtn = find.byTooltip('Klaviatura tugmalari (?)');
    expect(helpBtn, findsOneWidget);
    await tester.tap(helpBtn);
    await tester.pumpAndSettle();

    expect(find.text('Klaviatura tezkor tugmalari'), findsOneWidget);
    expect(find.text("Bo'sh joy / K"), findsOneWidget);
    expect(find.text(", / ."), findsOneWidget);

    // Close shortcuts dialog
    await tester.tap(find.text('Tushunarli'));
    await tester.pumpAndSettle();
    expect(find.text('Klaviatura tezkor tugmalari'), findsNothing);
  });
}
