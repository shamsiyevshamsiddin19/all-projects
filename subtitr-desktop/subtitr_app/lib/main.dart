import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'screens/home_screen.dart';

void main() {
  runApp(const SubtitleApp());
}

class SubtitleApp extends StatelessWidget {
  const SubtitleApp({super.key, this.autoScan = true});

  final bool autoScan;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Subtitr Desktop',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark, // Force dark mode for premium AI aesthetic
      darkTheme: ThemeData(
        useMaterial3: true,
        colorScheme: const ColorScheme.dark(
          primary: Colors.white,
          onPrimary: Colors.black,
          secondary: Color(0xFFAAAAAA),
          onSecondary: Colors.white,
          surface: Color(0xFF0A0A0A),
          onSurface: Colors.white,
          surfaceContainerHighest: Color(0xFF141414), // For inputs/secondary blocks
          outline: Color(0xFF222222),
          outlineVariant: Color(0xFF1A1A1A),
        ),
        scaffoldBackgroundColor: const Color(0xFF000000), // Pure black
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF000000),
          surfaceTintColor: Colors.transparent,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          color: const Color(0xFF0A0A0A),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: const BorderSide(color: Color(0xFF222222), width: 1),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: Colors.white,
            foregroundColor: Colors.black,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(30), // Pill shape like in image
            ),
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
            elevation: 0,
            textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(30),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            side: const BorderSide(color: Color(0xFF333333), width: 1.5),
            textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF0A0A0A),
          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF222222)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Color(0xFF222222)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: const BorderSide(color: Colors.white),
          ),
          labelStyle: const TextStyle(color: Color(0xFFAAAAAA)),
        ),
      ),
      home: HomeScreen(autoScan: autoScan),
    );
  }
}
