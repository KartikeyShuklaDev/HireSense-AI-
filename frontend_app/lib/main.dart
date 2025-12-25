import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';
import 'utils/helpers.dart';

void main() {
  // Ensure status bar style matches our theme
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
  ));
  runApp(const InterviewApp());
}

class InterviewApp extends StatelessWidget {
  const InterviewApp({super.key});

  // Define our custom palette
  static const Color manchesterGreen = Color(0xFF1A5E41); // Deep, rich green
  static const Color cozyBlue = Color(0xFF5D8AA8); // Soft, air-force blue
  static const Color surfaceWhite =
      Color(0xFFF8F9FA); // Off-white for better eye comfort

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Interview',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.light,
        scaffoldBackgroundColor: surfaceWhite,

        // Define the Color Scheme
        colorScheme: ColorScheme.fromSeed(
          seedColor: manchesterGreen,
          primary: manchesterGreen,
          secondary: cozyBlue,
          surface: surfaceWhite,
          onPrimary: Colors.white,
          onSecondary: Colors.white,
        ),

        // Modern Text Theme
        textTheme: const TextTheme(
          displayLarge:
              TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
          displayMedium:
              TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1E293B)),
          bodyLarge: TextStyle(color: Color(0xFF334155)),
        ),

        // Refined Card Theme
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 2,
          shadowColor: Colors.black.withOpacitySafe(0.05),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
        ),

        // Modern Button Styling
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: manchesterGreen,
            foregroundColor: Colors.white,
            elevation: 4,
            shadowColor: manchesterGreen.withOpacitySafe(0.4),
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 20),
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            textStyle:
                const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
        ),

        // Clean AppBar
        appBarTheme: const AppBarTheme(
          elevation: 0,
          backgroundColor: Colors.transparent,
          centerTitle: true,
          scrolledUnderElevation: 0,
          iconTheme: IconThemeData(color: Color(0xFF1E293B)),
          titleTextStyle: TextStyle(
            color: Color(0xFF1E293B),
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
