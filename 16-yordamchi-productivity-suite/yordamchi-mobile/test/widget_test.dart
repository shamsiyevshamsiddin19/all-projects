// Ilova ishga tushishining eng sodda tekshiruvi.
//
// Testda platforma kanallari (hujjatlar papkasi) mavjud emas, ya'ni
// `_boot()` xato beradi. Aynan shu holat sinaladi: ilova YIQILMASLIGI
// va foydalanuvchiga tushunarli ekran ko'rsatishi kerak. Ilgari bunday
// himoya yo'q edi va xato bo'lsa ilova qora ekranda qolib ketardi.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:yordamchi_app/main.dart';

void main() {
  testWidgets('Ilova yiqilmasdan ochiladi', (WidgetTester tester) async {
    await tester.pumpWidget(const YordamchiApp());
    await tester.pump();

    // Yuklanish indikatori yoki xato ekrani — ikkalasi ham to'g'ri holat.
    final loading = find.byType(CircularProgressIndicator);
    final failed = find.text('Ilova ochilmadi');
    expect(loading.evaluate().isNotEmpty || failed.evaluate().isNotEmpty, isTrue);
  });
}
