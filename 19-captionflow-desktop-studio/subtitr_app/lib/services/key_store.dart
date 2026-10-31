import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

/// Stores the user's API keys in a file only they can read.
///
/// They used to live in SharedPreferences, whose JSON file is created
/// world-readable (-rw-rw-r--): every other account and every process on the
/// machine could read a paid API key straight off disk. Backup and sync tools
/// pick that file up too.
///
/// This writes a separate file with 0600 and keeps the non-secret settings
/// (model overrides, appearance, last result) in SharedPreferences where they
/// belong. It is not encryption — a keyring (flutter_secure_storage via
/// libsecret) would be the next step, and would add another system dependency
/// on Linux. Owner-only permissions remove the exposure that actually matters
/// on a desktop: other local accounts, stray backups, a config folder shared
/// by accident.
class KeyStore {
  KeyStore({Directory? directory}) : _override = directory;

  final Directory? _override;
  File? _cached;

  static const _fileName = 'api_keys.json';

  Future<File> _file() async {
    final cached = _cached;
    if (cached != null) return cached;
    final dir = _override ?? await getApplicationSupportDirectory();
    await dir.create(recursive: true);
    return _cached = File('${dir.path}${Platform.pathSeparator}$_fileName');
  }

  Future<Map<String, String>> read() async {
    final file = await _file();
    if (!await file.exists()) return {};
    try {
      final raw = jsonDecode(await file.readAsString());
      if (raw is! Map) return {};
      return {
        for (final entry in raw.entries)
          if (entry.value is String) '${entry.key}': entry.value as String,
      };
    } catch (_) {
      // Buzilgan fayl — kalitlar yo'q deb hisoblaymiz. Ilova ochilsin,
      // foydalanuvchi qaytadan kiritadi.
      return {};
    }
  }

  Future<void> write(Map<String, String> keys) async {
    final file = await _file();
    final kept = {
      for (final entry in keys.entries)
        if (entry.value.trim().isNotEmpty) entry.key: entry.value.trim(),
    };
    if (kept.isEmpty) {
      if (await file.exists()) await file.delete();
      return;
    }
    // Avval fayl yaratiladi, KEYIN ruxsat toraytiriladi va faqat shundan
    // keyin kalit yoziladi — aks holda yozish bilan chmod orasida fayl
    // bir lahza hamma uchun ochiq qoladi.
    await file.writeAsString('{}');
    await restrict(file);
    await file.writeAsString(jsonEncode(kept), flush: true);
  }

  /// Makes [file] readable by its owner only.
  ///
  /// Dart has no chmod, so this shells out. On Windows the NTFS ACL on the
  /// user's AppData folder already limits access, so it is a no-op there.
  static Future<void> restrict(File file) async {
    if (Platform.isWindows) return;
    try {
      await Process.run('chmod', ['600', file.path]);
    } catch (_) {
      // chmod yo'q bo'lsa ham kalitlar saqlanadi — ruxsat kengroq qoladi.
    }
  }

  /// Moves keys out of SharedPreferences on first run after the upgrade.
  ///
  /// Returns the keys that were migrated so the caller can clear them from
  /// the old store. Without this an existing user's keys would stay in the
  /// world-readable file forever.
  Future<Map<String, String>> migrateFrom(
    Map<String, String?> legacy,
  ) async {
    final existing = await read();
    if (existing.isNotEmpty) return const {};
    final found = {
      for (final entry in legacy.entries)
        if ((entry.value ?? '').trim().isNotEmpty) entry.key: entry.value!.trim(),
    };
    if (found.isEmpty) return const {};
    await write(found);
    return found;
  }
}
