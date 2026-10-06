import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart' show rootBundle;

import 'store.dart';

/// Ilova ichidagi kichik HTTP server.
///
/// NIMA UCHUN SERVER, NEGA `file://` EMAS
/// --------------------------------------
/// Sayt kodi 25 000 qatordan ortiq va u oddiy veb-ilova sifatida yozilgan:
/// `fetch('/api?action=...')`, `localStorage`, service worker. Agar WebView
/// faylni to'g'ridan-to'g'ri `file://` orqali ochsa, brauzer uni "origin'siz"
/// deb biladi va `fetch` ham, `localStorage` ham ishlamaydi — butun ilova
/// yiqiladi.
///
/// Shuning uchun ilova ichida `127.0.0.1` da haqiqiy HTTP server ko'tariladi.
/// Natijada sayt kodi O'ZGARISHSIZ ishlaydi: u uchun bu oddiy veb-sayt,
/// `App.api = '/api'` esa aynan shu serverga tushadi.
///
/// Server ikki narsani beradi:
///   1. Statik fayllar — APK ichiga joylangan `assets/www/` dan
///   2. `/api` — internetsiz javob beradigan soddalashtirilgan backend
class LocalServer {
  final Store store;
  HttpServer? _server;
  Map<String, dynamic>? _snapshot;

  LocalServer(this.store);

  int get port => _server?.port ?? 0;
  String get origin => 'http://127.0.0.1:$port';

  Future<void> start() async {
    // Faqat qurilmaning o'zidan ulanish mumkin: loopback.
    // Tashqi tarmoqqa ochilsa, bir Wi-Fi'dagi boshqa qurilma
    // foydalanuvchining lug'ati va tarixini o'qiy olardi.
    _server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    _server!.listen(_handle, onError: (_) {});
  }

  Future<void> stop() async {
    await _server?.close(force: true);
    _server = null;
  }

  Future<Map<String, dynamic>> _snap() async {
    // 5.6 MB — bir marta o'qib, xotirada ushlab turamiz.
    _snapshot ??= jsonDecode(
      await rootBundle.loadString('assets/data/snapshot.json'),
    ) as Map<String, dynamic>;
    return _snapshot!;
  }

  Future<void> _handle(HttpRequest req) async {
    try {
      final path = req.uri.path;
      if (path == '/api') {
        await _api(req);
      } else {
        await _static(req, path);
      }
    } catch (e) {
      req.response.statusCode = 500;
      req.response.headers.contentType = ContentType.json;
      req.response.write(jsonEncode({'success': false, 'error': '$e'}));
    }
    await req.response.close();
  }

  // ---------------- Statik fayllar ----------------

  static const _mime = {
    'html': 'text/html; charset=utf-8',
    'js': 'application/javascript; charset=utf-8',
    'css': 'text/css; charset=utf-8',
    'json': 'application/json; charset=utf-8',
    'webmanifest': 'application/manifest+json; charset=utf-8',
    'md': 'text/markdown; charset=utf-8',
    'svg': 'image/svg+xml',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
    'ico': 'image/x-icon',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
  };

  Future<void> _static(HttpRequest req, String path) async {
    var rel = path == '/' ? '/index.html' : path;
    rel = Uri.decodeComponent(rel);
    // `?v=...` allaqachon `uri.path` ga kirmaydi, lekin ehtiyot uchun
    final q = rel.indexOf('?');
    if (q >= 0) rel = rel.substring(0, q);

    final key = 'assets/www$rel';
    try {
      final data = await rootBundle.load(key);
      final ext = rel.contains('.') ? rel.split('.').last.toLowerCase() : '';
      req.response.headers.set(
          HttpHeaders.contentTypeHeader, _mime[ext] ?? 'application/octet-stream');
      // Ichki server — keshlash shart emas, doim yangi fayl beriladi.
      req.response.headers.set(HttpHeaders.cacheControlHeader, 'no-store');
      req.response.add(data.buffer.asUint8List(
        data.offsetInBytes,
        data.lengthInBytes,
      ));
    } catch (_) {
      // SPA: mavjud bo'lmagan yo'l index.html ga tushadi (router o'zi hal qiladi)
      if (!rel.contains('.')) {
        final data = await rootBundle.load('assets/www/index.html');
        req.response.headers
            .set(HttpHeaders.contentTypeHeader, _mime['html']!);
        req.response.add(data.buffer.asUint8List(
          data.offsetInBytes,
          data.lengthInBytes,
        ));
      } else {
        req.response.statusCode = 404;
        req.response.write('not found');
      }
    }
  }

  // ---------------- Oflayn API ----------------

  Future<void> _api(HttpRequest req) async {
    final action = req.uri.queryParameters['action'] ?? '';
    Map<String, dynamic> body = {};
    if (req.method == 'POST') {
      final raw = await utf8.decoder.bind(req).join();
      if (raw.trim().isNotEmpty) {
        try {
          body = jsonDecode(raw) as Map<String, dynamic>;
        } catch (_) {}
      }
    }

    final res = await _dispatch(action, req.uri.queryParameters, body);
    await store.flush();

    req.response.headers.contentType = ContentType.json;
    req.response.headers.set(HttpHeaders.cacheControlHeader, 'no-store');
    req.response.write(jsonEncode(res));
  }

  Map<String, dynamic> _ok([Map<String, dynamic>? payload]) =>
      {'success': true, ...?payload};

  /// Backenddan aynan olingan tayyor javob (snapshot ichida saqlanadi).
  Future<Map<String, dynamic>> _canned(String key) async {
    final c = (await _snap())['canned'];
    if (c is Map && c[key] is Map) {
      return Map<String, dynamic>.from(c[key] as Map);
    }
    return _ok();
  }

  Future<Map<String, dynamic>> _dispatch(
      String action, Map<String, String> q, Map<String, dynamic> body) async {
    // Kirish tekshiruvi `?action=` SIZ yuboriladi — auth.js `amal` maydonini
    // ishlatadi. Oflayn ilovada kirish umuman kerak emas: ma'lumot shu
    // qurilmada, egasining o'zida.
    final amal = body['amal'];
    if (action.isEmpty && amal != null) {
      if (amal == 'sessiya_tekshir') {
        return {
          'holat': true,
          'kirganmi': true,
          'sozlanganmi': true,
          'himoya': false,
          'kirish_usuli': 'offline',
          'ism': 'Yordamchi',
        };
      }
      return {'holat': true};
    }

    switch (action) {
      // ---- Lug'at ----
      case 'get_dict_data':
        {
          final lang = (q['lang'] == 'english') ? 'english' : 'russian';
          final d = (await _snap())['dict'] as Map<String, dynamic>;
          final v = (d[lang] as Map).cast<String, dynamic>();
          return _ok({'items': v['items'], 'order': v['order']});
        }

      // ---- Til materiallari (.md) ----
      case 'get_topics':
        {
          final lang = q['lang'] ?? '';
          final all = (await _snap())['topics'] as List;
          final items = all
              .where((t) => lang.isEmpty || t['lang'] == lang)
              // Ro'yxatda mazmun kerak emas — u og'ir va faqat ochilganda o'qiladi
              .map((t) => {
                    'id': t['id'],
                    'lang': t['lang'],
                    'folder': t['folder'],
                    'name': t['name'],
                    // Kutubxona papka/fayl ajratishda shunga qaraydi
                    'has_content':
                        (t['content'] ?? '').toString().isNotEmpty,
                  })
              .toList();
          return _ok({'topics': items, 'items': items});
        }
      case 'get_topic':
        {
          final id = int.tryParse(q['id'] ?? '') ?? -1;
          final all = (await _snap())['topics'] as List;
          for (final t in all) {
            if (t['id'] == id) return _ok(Map<String, dynamic>.from(t));
          }
          return {'success': false, 'error': 'Material topilmadi'};
        }

      // ---- Sozlama/holat xotirasi (remote-storage.js) ----
      case 'storage_bootstrap':
        return _ok({'items': store.storage, 'storage': store.storage});
      case 'storage_set':
        {
          final k = body['key']?.toString();
          if (k != null) {
            store.storage[k] = body['value'];
            store.touch();
          }
          return _ok();
        }
      case 'storage_delete':
        {
          final k = body['key']?.toString();
          if (k != null) {
            store.storage.remove(k);
            store.touch();
          }
          return _ok();
        }

      // ---- Xatolar ustida ishlash ----
      case 'get_mistakes':
        return _ok({'mistakes': store.mistakes(q['lang'] ?? 'russian')});
      case 'add_mistake':
        {
          final lang = body['lang']?.toString() ?? 'russian';
          final list = store.mistakes(lang);
          final ru = body['ru']?.toString() ?? '';
          final cat = body['category']?.toString() ?? '';
          final exists = list.any((m) => m['word_ru'] == ru && m['category'] == cat);
          if (!exists && ru.isNotEmpty) {
            list.add({
              'word_ru': ru,
              'word_uz': body['uz']?.toString() ?? '',
              'category': cat,
            });
            store.touch();
          }
          return _ok();
        }
      case 'remove_mistake':
        {
          final lang = body['lang']?.toString() ?? 'russian';
          final list = store.mistakes(lang);
          final ru = body['ru']?.toString() ?? '';
          final cat = body['category']?.toString() ?? '';
          list.removeWhere((m) => m['word_ru'] == ru && m['category'] == cat);
          store.touch();
          return _ok();
        }

      // ---- Faollik tarixi ----
      case 'log_activity':
        {
          store.activity.add({
            ...body,
            'created_at': DateTime.now().toIso8601String(),
          });
          // Ro'yxat cheksiz o'smasin
          if (store.activity.length > 2000) {
            store.activity.removeRange(0, store.activity.length - 2000);
          }
          store.touch();
          return _ok();
        }
      case 'get_activity_log':
        return _ok({'items': store.activity, 'log': store.activity});

      // ---- Testlar, Sport, Maqsadlar ----
      // Bu javoblar backendning O'ZIDAN aynan olingan (snapshot > canned),
      // shakli taxmin qilinmagan — jonli sayt bilan bir xil.
      case 'get_structure':
        return _canned('get_structure');
      case 'get_quiz_results':
        return _canned('quiz_results');
      case 'sport_get_all':
        return _canned('sport_get_all');
      case 'get_data':
        {
          // `Global_Data` — maqsadlar/bo'limlar. Boshqa bazalar (testlar)
          // hozircha bo'sh: quiz_questions jadvali serverda ham bo'sh.
          final name = (q['db'] ?? '').trim();
          if (name.isEmpty || name == 'Global_Data') return _canned('global_data');
          return _ok({'questions': [], 'solved': [], 'flags': []});
        }

      // ---- Jimgina yutiladiganlar ----
      case 'log_client':
      case 'save_state':
      // `storage_sync` — remote-storage.js serverga surish uchun chaqiradi.
      // Oflayn ilovada yozuvlar allaqachon diskda, sinxronlash kerak emas.
      case 'storage_sync':
        return _ok();

      default:
        // Boost (Telegram kanali) va LMS (universitet tizimi) TABIATAN
        // onlayn: ular boshqa serverlarga boradi, ularni qurilmaga
        // ko'chirib bo'lmaydi. Shuning uchun xabar aniq bo'lsin —
        // foydalanuvchi "ilova buzuq" deb o'ylamasin.
        if (action.startsWith('boost_') || action.startsWith('lms_')) {
          return {
            'success': false,
            'error': 'Bu bo\'lim internet talab qiladi (oflayn rejimda ishlamaydi).',
          };
        }
        return {
          'success': false,
          'error': 'Bu amal oflayn rejimda mavjud emas: $action',
        };
    }
  }
}
