import 'package:flutter/material.dart';

class Helpers {
  /// Capitalizes the first letter of a string.
  /// Example: "interview" -> "Interview"
  static String capitalize(String s) {
    if (s.isEmpty) return s;
    return s[0].toUpperCase() + s.substring(1);
  }
}

/// Extension to provide a non-deprecated opacity helper. Uses integer alpha
/// under the hood to avoid the precision-loss warning from `withOpacity`.
extension ColorExtensions on Color {
  /// Returns a color with the given opacity (0.0 - 1.0) using `withAlpha`.
  Color withOpacitySafe(double opacity) {
    assert(opacity >= 0 && opacity <= 1);
    return withAlpha((opacity * 255).round());
  }
}
