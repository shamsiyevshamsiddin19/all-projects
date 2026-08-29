import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'local_server.dart';
import 'store.dart';

/// Yordamchi — OFLAYN ilova.
///
/// Ilgari bu ilova shunchaki `https://y.wstore.uz` ni WebView'da ochardi.
/// Undan ikki jiddiy muammo kelib chiqqan edi:
///
///   1. Internet bo'lmasa ilova umuman ishlamasdi (bo'sh ekran).
///   2. Sayt Google bilan qulflangach kirish MUMKIN EMAS bo'lib qoldi:
///      Google o'rnatilgan WebView ichida OAuth'ni ataylab bloklaydi
///      (`disallowed_useragent`). Ya'ni ilova butunlay foydasiz edi.
///
/// Endi sayt APK ICHIDA turadi va ilova o'z ichida kichik HTTP server
/// ko'taradi (`local_server.dart`). WebView o'sha serverga ulanadi.
/// Natijada: internet umuman kerak emas, kirish ham kerak emas —
/// ma'lumot qurilmaning o'zida.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: Color(0xFF0F1216),
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const YordamchiApp());
}

class YordamchiApp extends StatelessWidget {
  const YordamchiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Yordamchi',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F1216),
      ),
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final Store _store = Store();
  LocalServer? _server;
  WebViewController? _controller;
  String? _error;

  @override
  void initState() {
    super.initState();
    _boot();
  }

  Future<void> _boot() async {
    try {
      await _store.init();
      final srv = LocalServer(_store);
      await srv.start();

      final c = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..setBackgroundColor(const Color(0xFF0F1216))
        ..setNavigationDelegate(
          NavigationDelegate(
            // Tashqi havolalar ilovani tark etmasin — ichki server
            // manzilidan boshqasiga o'tishga ruxsat bermaymiz.
            onNavigationRequest: (req) {
              if (req.url.startsWith(srv.origin)) {
                return NavigationDecision.navigate;
              }
              return NavigationDecision.prevent;
            },
            onWebResourceError: (e) {
              // Bitta rasm yuklanmasa ham butun ilovani yiqitmaymiz;
              // faqat asosiy hujjat yiqilsa xabar beramiz.
              if (e.isForMainFrame == true) {
                setState(() => _error = e.description);
              }
            },
          ),
        )
        ..loadRequest(Uri.parse(srv.origin));

      if (!mounted) return;
      setState(() {
        _server = srv;
        _controller = c;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    }
  }

  @override
  void dispose() {
    _server?.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = _controller;

    if (_error != null) {
      return Scaffold(
        backgroundColor: const Color(0xFF0F1216),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline, color: Color(0xFFF0564B), size: 44),
                const SizedBox(height: 14),
                const Text('Ilova ochilmadi',
                    style: TextStyle(
                        color: Color(0xFFE7ECF3),
                        fontSize: 18,
                        fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text(_error!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Color(0xFF7B8798), fontSize: 13)),
                const SizedBox(height: 18),
                FilledButton(
                  onPressed: () {
                    setState(() => _error = null);
                    _boot();
                  },
                  child: const Text('Qayta urinish'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (c == null) {
      return const Scaffold(
        backgroundColor: Color(0xFF0F1216),
        body: Center(
          child: CircularProgressIndicator(color: Color(0xFF2CBB5D)),
        ),
      );
    }

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        if (await c.canGoBack()) {
          await c.goBack();
        } else {
          SystemNavigator.pop();
        }
      },
      child: Scaffold(
        backgroundColor: const Color(0xFF0F1216),
        body: SafeArea(child: WebViewWidget(controller: c)),
      ),
    );
  }
}
