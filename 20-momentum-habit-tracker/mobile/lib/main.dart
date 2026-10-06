import 'package:device_preview/device_preview.dart';
import 'package:flutter/foundation.dart' show kReleaseMode;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'features/assignments/assignment_provider.dart';
import 'features/auth/auth_provider.dart';
import 'features/groups/group_provider.dart';
import 'features/reports/analytics_provider.dart';
import 'features/standalone/standalone_provider.dart';
import 'features/standalone/teacher_home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => StandaloneProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => GroupProvider()),
        ChangeNotifierProvider(create: (_) => AssignmentProvider()),
        ChangeNotifierProvider(create: (_) => AnalyticsProvider()),
      ],
      // Qurilma ko'rinishi paneli: iPhone, Android, iPad, Mac, Windows
      // rusumlarini tanlab ko'rish uchun. Release build'da o'chiq.
      child: DevicePreview(
        enabled: !kReleaseMode,
        builder: (_) => const TrackerApp(),
      ),
    ),
  );
}

class TrackerApp extends StatelessWidget {
  const TrackerApp({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return MaterialApp(
      title: 'Tracker Teacher App',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: auth.themeMode,
      locale: DevicePreview.locale(context),
      builder: DevicePreview.appBuilder,
      home: const TeacherHomeScreen(),
    );
  }
}
