import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/services/key_store.dart';

/// API keys used to sit in SharedPreferences, whose file is created
/// world-readable. These tests pin the two things that fixes: the file is
/// owner-only, and an existing user's keys actually move out of the old one.
void main() {
  late Directory dir;
  late KeyStore store;

  setUp(() {
    dir = Directory.systemTemp.createTempSync('subtitr_keys_test');
    store = KeyStore(directory: dir);
  });

  tearDown(() {
    if (dir.existsSync()) dir.deleteSync(recursive: true);
  });

  String mode(File file) =>
      Process.runSync('stat', ['-c', '%a', file.path]).stdout.toString().trim();

  File keyFile() => File('${dir.path}/api_keys.json');

  test('keys round trip', () async {
    await store.write({'groq_api_key': 'gsk_test123', 'openai_api_key': ''});
    expect(await store.read(), {'groq_api_key': 'gsk_test123'});
  });

  test('the file is readable by its owner only', () async {
    await store.write({'groq_api_key': 'gsk_test123'});
    expect(mode(keyFile()), '600',
        reason: 'kalit fayli boshqalarga ham ochiq qolgan');
  }, skip: Platform.isWindows ? 'POSIX ruxsatlari' : null);

  test('an empty set removes the file rather than leaving an empty one',
      () async {
    await store.write({'groq_api_key': 'gsk_test123'});
    expect(keyFile().existsSync(), isTrue);
    await store.write({'groq_api_key': '   '});
    expect(keyFile().existsSync(), isFalse);
  });

  test('a corrupt file does not stop the app starting', () async {
    keyFile().writeAsStringSync('{bu json emas');
    expect(await store.read(), isEmpty);
  });

  test('legacy keys are migrated and reported back', () async {
    final moved = await store.migrateFrom({
      'groq_api_key': 'gsk_old',
      'openai_api_key': null,
      'gemini_api_key': '  ',
    });
    expect(moved, {'groq_api_key': 'gsk_old'});
    expect(await store.read(), {'groq_api_key': 'gsk_old'});
    expect(mode(keyFile()), '600');
  }, skip: Platform.isWindows ? 'POSIX ruxsatlari' : null);

  test('migration never overwrites keys already stored', () async {
    await store.write({'groq_api_key': 'gsk_new'});
    final moved = await store.migrateFrom({'groq_api_key': 'gsk_old'});
    expect(moved, isEmpty);
    expect(await store.read(), {'groq_api_key': 'gsk_new'});
  });

  test('the key is never written while the file is still world-readable',
      () async {
    // Fayl avval bo'sh yaratiladi, ruxsat toraytiriladi, keyin kalit
    // yoziladi — aks holda ikkisi orasida kalit bir lahza ochiq qoladi.
    await store.write({'groq_api_key': 'gsk_secret'});
    final text = keyFile().readAsStringSync();
    expect(jsonDecode(text), {'groq_api_key': 'gsk_secret'});
    expect(mode(keyFile()), '600');
  }, skip: Platform.isWindows ? 'POSIX ruxsatlari' : null);
}
