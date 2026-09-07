import 'dart:io';
import 'package:excel/excel.dart' as ex;
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'local_storage_service.dart';

class LocalExportService {
  static Future<String?> exportGroupPdf({
    required LocalGroup group,
    required List<LocalTask> tasks,
    required List<LocalRecord> records,
  }) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        build: (pw.Context context) {
          return [
            pw.Header(
              level: 0,
              child: pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text(
                    'TRACKER APP - O\'quv Hisoboti',
                    style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold),
                  ),
                  pw.Text(
                    DateTime.now().toString().split(' ')[0],
                    style: const pw.TextStyle(fontSize: 12, color: PdfColors.grey700),
                  ),
                ],
              ),
            ),
            pw.SizedBox(height: 12),
            pw.Container(
              padding: const pw.EdgeInsets.all(12),
              decoration: pw.BoxDecoration(
                color: PdfColors.indigo50,
                borderRadius: pw.BorderRadius.circular(8),
              ),
              child: pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.start,
                children: [
                  pw.Text('Guruh: ${group.name}', style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold, color: PdfColors.indigo900)),
                  if (group.description != null) pw.Text('Tavsif: ${group.description!}', style: const pw.TextStyle(fontSize: 11, color: PdfColors.grey700)),
                  pw.Text('Jami talabalar: ${group.students.length} nafar | Vazifalar: ${tasks.length} ta', style: const pw.TextStyle(fontSize: 11)),
                ],
              ),
            ),
            pw.SizedBox(height: 20),
            pw.Text('Talabalar va Vazifalar O\'zlashtirish Jadvali:', style: pw.TextStyle(fontSize: 13, fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 8),
            pw.TableHelper.fromTextArray(
              headers: ['№', 'Talaba Ismi', 'Telefon', ...tasks.map((t) => t.title.length > 15 ? '${t.title.substring(0, 12)}...' : t.title), 'Bajarildi', 'O\'rtacha'],
              headerStyle: pw.TextStyle(fontWeight: pw.FontWeight.bold, color: PdfColors.white, fontSize: 9),
              headerDecoration: const pw.BoxDecoration(color: PdfColors.indigo600),
              cellHeight: 25,
              cellAlignments: {0: pw.Alignment.centerLeft},
              cellStyle: const pw.TextStyle(fontSize: 8.5),
              data: List<List<dynamic>>.generate(
                group.students.length,
                (index) {
                  final st = group.students[index];
                  int doneCount = 0;
                  int totalScore = 0;

                  List<String> taskStatuses = tasks.map((t) {
                    final rec = records.where((r) => r.taskId == t.id && r.studentId == st.id).firstOrNull;
                    if (rec != null && rec.isDone) {
                      doneCount++;
                      totalScore += rec.score;
                      return '${rec.score} ball [OK]';
                    }
                    return '-';
                  }).toList();

                  double avg = tasks.isNotEmpty ? (totalScore / tasks.length) : 0.0;

                  return [
                    '${index + 1}',
                    st.name,
                    st.phone ?? '-',
                    ...taskStatuses,
                    '$doneCount/${tasks.length}',
                    avg.toStringAsFixed(1),
                  ];
                },
              ),
            ),
            pw.SizedBox(height: 30),
            pw.Divider(),
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              children: [
                pw.Text('O\'qituvchi imzosi: ___________________', style: const pw.TextStyle(fontSize: 10, color: PdfColors.grey700)),
                pw.Text('Tracker Standalone Engine', style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey500)),
              ],
            ),
          ];
        },
      ),
    );

    final file = await _exportFile('Tracker_Guruh_${group.name.replaceAll(' ', '_')}.pdf');
    await file.writeAsBytes(await pdf.save());
    await OpenFilex.open(file.path);
    return file.path;
  }

  static Future<String?> exportGroupExcel({
    required LocalGroup group,
    required List<LocalTask> tasks,
    required List<LocalRecord> records,
  }) async {
    final excel = ex.Excel.createExcel();
    final sheetName = 'Guruh_${group.name.length > 20 ? group.name.substring(0, 20) : group.name}';
    final sheet = excel[sheetName];
    excel.setDefaultSheet(sheetName);

    // Headers
    List<ex.CellValue> headers = [
      ex.TextCellValue('№'),
      ex.TextCellValue('Talaba Ismi'),
      ex.TextCellValue('Telefon'),
      ...tasks.map((t) => ex.TextCellValue(t.title)),
      ex.TextCellValue('Jami Bajarilgan'),
      ex.TextCellValue('O\'rtacha Ball'),
    ];
    sheet.appendRow(headers);

    // Rows
    for (int i = 0; i < group.students.length; i++) {
      final st = group.students[i];
      int doneCount = 0;
      int totalScore = 0;

      List<ex.CellValue> taskCells = tasks.map((t) {
        final rec = records.where((r) => r.taskId == t.id && r.studentId == st.id).firstOrNull;
        if (rec != null && rec.isDone) {
          doneCount++;
          totalScore += rec.score;
          return ex.TextCellValue('${rec.score} (Bajarildi)');
        }
        return ex.TextCellValue('Bajarilmadi');
      }).toList();

      double avg = tasks.isNotEmpty ? (totalScore / tasks.length) : 0.0;

      sheet.appendRow([
        ex.IntCellValue(i + 1),
        ex.TextCellValue(st.name),
        ex.TextCellValue(st.phone ?? ''),
        ...taskCells,
        ex.TextCellValue('$doneCount / ${tasks.length}'),
        ex.DoubleCellValue(avg),
      ]);
    }

    final file = await _exportFile('Tracker_Guruh_${group.name.replaceAll(' ', '_')}.xlsx');
    final fileBytes = excel.save();
    if (fileBytes != null) {
      await file.writeAsBytes(fileBytes);
      await OpenFilex.open(file.path);
      return file.path;
    }
    return null;
  }

  /// Hisobot doimiy joyga saqlanadigan yo'lni qaytaradi. Avval
  /// `getTemporaryDirectory()` ishlatilgan edi — u OS tomonidan istalgan
  /// payt, hatto o'qituvchi faylni ochib ko'rgan zahotiyoq tozalanib
  /// ketishi mumkin bo'lgan keshdir. Ilova hujjatlar papkasi (yoki
  /// mavjud bo'lsa qurilmaning "Yuklab olingan fayllar" papkasi) ilova
  /// o'chirilmaguncha saqlanib qoladi.
  static Future<File> _exportFile(String fileName) async {
    Directory dir;
    try {
      dir = await getDownloadsDirectory() ?? await getApplicationDocumentsDirectory();
    } catch (_) {
      dir = await getApplicationDocumentsDirectory();
    }
    final exportsDir = Directory('${dir.path}/Tracker_Hisobotlar');
    if (!await exportsDir.exists()) {
      await exportsDir.create(recursive: true);
    }
    return File('${exportsDir.path}/$fileName');
  }
}
