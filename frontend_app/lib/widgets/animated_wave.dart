import 'package:flutter/material.dart';
import '../utils/helpers.dart';
import 'dart:math' as math;

class AnimatedWave extends StatefulWidget {
  const AnimatedWave({super.key});

  @override
  State<AnimatedWave> createState() => _AnimatedWaveState();
}

class _AnimatedWaveState extends State<AnimatedWave>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 5), // Slower, cozier speed
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          painter: WavePainter(_controller.value),
          child: Container(),
        );
      },
    );
  }
}

class WavePainter extends CustomPainter {
  final double animationValue;

  WavePainter(this.animationValue);

  // Theme Colors
  static const Color manchesterGreen = Color(0xFF1A5E41);
  static const Color cozyBlue = Color(0xFF5D8AA8);

  @override
  void paint(Canvas canvas, Size size) {
    // Wave 1: Cozy Blue (Background, taller)
    final paint1 = Paint()
      ..color = cozyBlue.withOpacitySafe(0.15)
      ..style = PaintingStyle.fill;

    // Wave 2: Manchester Green (Foreground, slightly lower)
    final paint2 = Paint()
      ..color = manchesterGreen.withOpacitySafe(0.1)
      ..style = PaintingStyle.fill;

    final path1 = Path();
    final path2 = Path();

    // First wave calculation (Blue)
    path1.moveTo(0, size.height * 0.7);
    for (double i = 0; i <= size.width; i++) {
      path1.lineTo(
        i,
        size.height * 0.7 +
            math.sin((i / size.width * 2 * math.pi) +
                    (animationValue * 2 * math.pi)) *
                25, // Amplitude
      );
    }
    path1.lineTo(size.width, size.height);
    path1.lineTo(0, size.height);
    path1.close();

    // Second wave calculation (Green) - Phase shifted
    path2.moveTo(0, size.height * 0.75);
    for (double i = 0; i <= size.width; i++) {
      path2.lineTo(
        i,
        size.height * 0.75 +
            math.sin((i / size.width * 2 * math.pi) +
                    (animationValue * 2 * math.pi) +
                    2.5) * // Different phase shift
                20, // Different Amplitude
      );
    }
    path2.lineTo(size.width, size.height);
    path2.lineTo(0, size.height);
    path2.close();

    // Draw Blue first (behind), then Green (front)
    canvas.drawPath(path1, paint1);
    canvas.drawPath(path2, paint2);
  }

  @override
  bool shouldRepaint(WavePainter oldDelegate) {
    return oldDelegate.animationValue != animationValue;
  }
}
