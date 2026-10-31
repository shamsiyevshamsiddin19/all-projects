import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
// Test ham ekrandagi versiya manbasini bevosita soxtalashtiradi; pubspec
// fayli qat'iy chegaradan tashqarida bo'lgani uchun linter eslatmasini bosamiz.
// ignore: depend_on_referenced_packages
import 'package:package_info_plus/package_info_plus.dart';
import 'package:subtitr_app/screens/api_keys_screen.dart';
import 'package:subtitr_app/screens/home_screen.dart';
import 'package:subtitr_app/screens/translation_editor_screen.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';
import 'package:subtitr_app/services/settings_store.dart';
import 'package:subtitr_app/widgets/processing_panel.dart';

/// Tahrirlash oynasida haqiqiy pleyer ishga tushmasligi uchun soxta servis.
/// Bu testlar fayl renderini emas, foydalanuvchi ko'radigan natijani tekshiradi.
class _EditorProcessor extends DesktopProcessorService {
  @override
  Future<({String subtitles, String video})> subtitleFile({
    required String sessionPath,
    required List<SubtitleSegment> segments,
    required String mode,
    double fontScale = 1.0,
    String position = 'bottom',
    String subColor = '#FFE680',
    String origStyle = 'box',
  }) async {
    throw StateError('testda pleyer yo\'q');
  }
}

SubtitleSegment _segment({
  String original = 'Noto\'g\'ri eshitilgan ism',
  String translated = 'Tarjima',
}) => SubtitleSegment(
  start: 0,
  end: 2,
  original: original,
  translated: translated,
);

PreparedSession _session(List<SubtitleSegment> segments) => PreparedSession(
  sessionPath: '/tmp/session.json',
  video: '/tmp/video.mp4',
  mode: 'dual',
  sourceLang: 'ru',
  targetLang: 'uz',
  transcriber: 'groq',
  translator: 'openai',
  segments: segments,
  vocabCount: 0,
);

class _EditorHandle {
  Future<List<SubtitleSegment>?>? result;
}

Future<_EditorHandle> _openEditor(
  WidgetTester tester,
  List<SubtitleSegment> segments,
) async {
  final handle = _EditorHandle();
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: Center(
          child: Builder(
            builder: (context) => FilledButton(
              onPressed: () {
                handle.result = Navigator.of(context)
                    .push<List<SubtitleSegment>>(
                      MaterialPageRoute(
                        builder: (_) => TranslationEditorScreen(
                          session: _session(segments),
                          service: _EditorProcessor(),
                        ),
                      ),
                    );
              },
              child: const Text('Muharrirni ochish'),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.tap(find.text('Muharrirni ochish'));
  await tester.pumpAndSettle();
  return handle;
}

Widget _processingPanel(DateTime lastProgressUpdate) => MaterialApp(
  home: Scaffold(
    body: SizedBox(
      width: 800,
      height: 500,
      child: ProcessingPanel(
        selectedName: 'film.mp4',
        selectedPath: '/tmp/film.mp4',
        outDir: '/tmp/out',
        isRunning: true,
        progress: 0.65,
        status: 'PDF yozilmoqda',
        result: null,
        startTime: DateTime.now().subtract(const Duration(minutes: 2)),
        lastProgressUpdate: lastProgressUpdate,
        onStart: () {},
        onOpenPath: (_) async {},
      ),
    ),
  ),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('tahrirlangan asl matn renderga JSON orqali yuboriladi', (
    tester,
  ) async {
    final segments = [_segment()];
    final handle = await _openEditor(tester, segments);

    await tester.tap(find.text('Noto\'g\'ri eshitilgan ism'));
    await tester.pump();
    await tester.enterText(
      find.byKey(const ValueKey('original-1')),
      'Alisher Navoiy',
    );
    await tester.tap(find.text('Videoni render qilish'));
    await tester.pumpAndSettle();

    final rendered = await handle.result!;
    expect(rendered, isNotNull);
    expect(rendered!.single.toJson()['original'], 'Alisher Navoiy');
  });

  testWidgets('o‘zgarmagan muharrirdan chiqish tasdiq so‘ramaydi', (
    tester,
  ) async {
    final handle = await _openEditor(tester, [_segment()]);

    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();

    expect(find.text('Tahrirlar saqlanmaydi'), findsNothing);
    expect(await handle.result!, isNull);
  });

  testWidgets(
    'tahrirlangan muharrirdan chiqish tasdiqlanadi va o‘zgarishni tashlaydi',
    (tester) async {
      final segments = [_segment()];
      final handle = await _openEditor(tester, segments);
      await tester.tap(find.text('Noto\'g\'ri eshitilgan ism'));
      await tester.pump();
      await tester.enterText(
        find.byKey(const ValueKey('original-1')),
        'Alisher Navoiy',
      );
      // Kiritilgan matn keyingi freymda PopScope holatiga o'tadi; haqiqiy
      // foydalanuvchi ham tahrirdan keyin aynan shu yangilangan oynani ko'radi.
      await tester.pump();

      await tester.binding.handlePopRoute();
      await tester.pumpAndSettle();
      expect(find.text('Chiqilsinmi? Tahrirlar saqlanmaydi.'), findsOneWidget);

      await tester.tap(find.text('Chiqish'));
      await tester.pumpAndSettle();

      expect(await handle.result!, isNull);
      expect(segments.single.original, 'Noto\'g\'ri eshitilgan ism');
    },
  );

  testWidgets(
    'uzoq vaqt yangilanmagan yakuniy progress hali ishlayotganini ko‘rsatadi',
    (tester) async {
      await tester.pumpWidget(
        _processingPanel(DateTime.now().subtract(const Duration(seconds: 16))),
      );
      expect(
        find.text('Hali ishlayapti — yakuniy fayllar yozilmoqda.'),
        findsOneWidget,
      );

      await tester.pumpWidget(_processingPanel(DateTime.now()));
      expect(
        find.text('Hali ishlayapti — yakuniy fayllar yozilmoqda.'),
        findsNothing,
      );
    },
  );

  testWidgets('sozlamalar pubspec versiyasini ko‘rsatadi', (tester) async {
    PackageInfo.setMockInitialValues(
      appName: 'Subtitr Desktop',
      packageName: 'uz.shamsiddin.subtitr',
      version: '1.0.0',
      buildNumber: '1',
      buildSignature: '',
    );
    await tester.binding.setSurfaceSize(const Size(900, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      const MaterialApp(
        home: ApiKeysScreen(initial: AppSettings(), loadCache: false),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Versiya 1.0.0+1'), findsOneWidget);
  });
  testWidgets('subtitr vaqtini (start va end) tahrirlash renderga saqlanadi', (
    tester,
  ) async {
    final segments = [_segment()];
    final handle = await _openEditor(tester, segments);

    // Vaqt ko'rsatkichini bosamiz
    await tester.tap(find.byKey(const ValueKey('timing-tile-1')));
    await tester.pumpAndSettle();

    expect(find.text('Vaqtni sozlash (#1)'), findsOneWidget);

    // +0.5s ikkalasi tugmasini bosamiz (0..2s -> 0.5..2.5s)
    await tester.tap(find.text('+0.5s ikkalasi'));
    await tester.pump();

    // Saqlash tugmasini bosamiz
    await tester.tap(find.byKey(const ValueKey('save-timing-button')));
    await tester.pumpAndSettle();

    expect(find.text('00:00.5 → 00:02.5'), findsOneWidget);

    // Render tugmasini bosamiz
    await tester.tap(find.text('Videoni render qilish'));
    await tester.pumpAndSettle();

    final rendered = await handle.result!;
    expect(rendered, isNotNull);
    expect(rendered!.single.start, 0.5);
    expect(rendered.single.end, 2.5);
  });

  testWidgets('asosiy ekranda versiya nishoni ko‘rinadi', (tester) async {
    PackageInfo.setMockInitialValues(
      appName: 'Subtitr Desktop',
      packageName: 'uz.shamsiddin.subtitr',
      version: '1.2.3',
      buildNumber: '4',
      buildSignature: '',
    );
    await tester.pumpWidget(
      const MaterialApp(
        home: HomeScreen(autoScan: false),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('v1.2.3+4'), findsOneWidget);
  });
}
