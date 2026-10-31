import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/screens/api_keys_screen.dart';
import 'package:subtitr_app/services/settings_store.dart';

/// `loadCache: false` — kesh hajmini o'qish Python jarayonini ishga tushiradi;
/// testda u kerak emas, bizga maketning o'zi muhim.
Widget _screen() => const MaterialApp(
      home: ApiKeysScreen(initial: AppSettings(), loadCache: false),
    );

void main() {
  testWidgets('Sozlamalar ekranida "Disk keshi" bo\'limi bor', (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(_screen());
    await tester.pump();

    expect(find.text('Sozlamalar'), findsOneWidget);
    expect(find.text('Disk keshi'), findsOneWidget);
    expect(find.textContaining('5 GB dan oshsa'), findsOneWidget);
  });

  testWidgets('eski mazmun joyida qoldi (faqat qo\'shildi)', (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(_screen());
    await tester.pump();

    expect(find.text('Groq API kalit'), findsOneWidget);
    expect(find.text('OpenAI API kalit'), findsOneWidget);
    expect(find.text('Saqlash'), findsOneWidget);
    expect(find.text('Kalitlarni ko\'rsatish'), findsOneWidget);
  });

  testWidgets('tor oynada sarlavha qatorlari toshmaydi', (tester) async {
    // Toshish `RenderFlex overflowed` xatosini beradi va test tushadi —
    // aynan shu xato "Qo'shimcha: model sozlamalari" qatorida bor edi.
    await tester.binding.setSurfaceSize(const Size(420, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(_screen());
    await tester.pump();

    expect(find.text('Disk keshi'), findsOneWidget);
  });
}
