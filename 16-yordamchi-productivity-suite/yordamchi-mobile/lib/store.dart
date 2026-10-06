import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

/// Ilovaning O'Z papkasidagi doimiy xotira.
///
/// NIMA UCHUN ALOHIDA PAPKA
/// ------------------------
/// Ilova internetsiz ishlaydi, ya'ni foydalanuvchi kiritgan hamma narsa —
/// o'rgangan so'zlar, xatolar, mashq tarixi, sozlamalar — faqat shu
/// qurilmada saqlanadi. Ular WebView'ning `localStorage`ida qolsa,
/// tizim keshni tozalaganda YO'QOLARDI. Shuning uchun hammasi ilovaning
/// hujjatlar papkasidagi oddiy JSON fayllarga yoziladi:
///
///   `<app-documents>/yordamchi/store.json`  — foydalanuvchi ma'lumoti
///   `<app-documents>/yordamchi/files/`      — yuklangan .md fayllar
///
/// Fayl formati ATAYLAB oddiy JSON: zaxira olish, ko'chirish yoki
/// qo'lda ko'rib chiqish oson bo'lsin.
class Store {
  late final Directory root;
  late final File _dbFile;
  Map<String, dynamic> _data = {};
  bool _dirty = false;

  Future<void> init() async {
    final docs = await getApplicationDocumentsDirectory();
    root = Directory('${docs.path}/yordamchi');
    if (!await root.exists()) {
      await root.create(recursive: true);
    }
    final files = Directory('${root.path}/files');
    if (!await files.exists()) {
      await files.create(recursive: true);
    }

    _dbFile = File('${root.path}/store.json');
    if (await _dbFile.exists()) {
      try {
        _data = jsonDecode(await _dbFile.readAsString()) as Map<String, dynamic>;
      } catch (_) {
        // Buzuq fayl ishni to'xtatmasin — eskisini chetga surib, toza boshlaymiz.
        try {
          await _dbFile.rename('${_dbFile.path}.buzuq');
        } catch (_) {}
        _data = {};
      }
    }
    _data.putIfAbsent('storage', () => <String, dynamic>{});
    _data.putIfAbsent('mistakes', () => <String, dynamic>{});
    _data.putIfAbsent('activity', () => <dynamic>[]);
  }

  Map<String, dynamic> get storage =>
      (_data['storage'] as Map).cast<String, dynamic>();

  /// `lang` bo'yicha xatolar ro'yxati
  List<dynamic> mistakes(String lang) {
    final m = (_data['mistakes'] as Map).cast<String, dynamic>();
    return (m[lang] ??= <dynamic>[]) as List<dynamic>;
  }

  List<dynamic> get activity => (_data['activity'] as List);

  void touch() => _dirty = true;

  /// Diskka yozish. Har o'zgarishda emas — chaqiruvchi `touch()` qilgach
  /// bir marta. Yozuv ATOMIK: avval vaqtinchalik faylga, keyin ko'chiriladi.
  /// Aks holda yozuv o'rtasida ilova yopilsa fayl yarim qolib buzilardi.
  Future<void> flush() async {
    if (!_dirty) return;
    _dirty = false;
    final tmp = File('${_dbFile.path}.tmp');
    await tmp.writeAsString(jsonEncode(_data), flush: true);
    await tmp.rename(_dbFile.path);
  }
}
