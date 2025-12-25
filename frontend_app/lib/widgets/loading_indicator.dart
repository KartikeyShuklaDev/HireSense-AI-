import 'package:flutter/material.dart';
import '../utils/helpers.dart';

class LoadingIndicator extends StatefulWidget {
  const LoadingIndicator({super.key});

  @override
  State<LoadingIndicator> createState() => _LoadingIndicatorState();
}

class _LoadingIndicatorState extends State<LoadingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _rotationAnimation;
  late Animation<double> _scaleAnimation;

  // Define Theme Colors
  static const Color manchesterGreen = Color(0xFF1A5E41);
  static const Color cozyBlue = Color(0xFF5D8AA8);
  static const Color slateText = Color(0xFF334155);

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    )..repeat();

    // Smoother rotation curve
    _rotationAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOutQuart, // More "elastic" feel
    ));

    // Gentle heartbeat scale
    _scaleAnimation = TweenSequence<double>([
      TweenSequenceItem(
        tween: Tween<double>(begin: 1.0, end: 1.15)
            .chain(CurveTween(curve: Curves.easeOutCubic)),
        weight: 50,
      ),
      TweenSequenceItem(
        tween: Tween<double>(begin: 1.15, end: 1.0)
            .chain(CurveTween(curve: Curves.easeInCubic)),
        weight: 50,
      ),
    ]).animate(_controller);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              return Transform.scale(
                scale: _scaleAnimation.value,
                child: Transform.rotate(
                  angle: _rotationAnimation.value * 2 * 3.14159,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      // The new trendy gradient: Green -> Blue
                      gradient: const LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          manchesterGreen,
                          cozyBlue,
                        ],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: manchesterGreen.withOpacitySafe(0.3),
                          blurRadius: 24,
                          offset: const Offset(0, 10),
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.psychology_rounded,
                      color: Colors.white,
                      size: 40,
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 40),
          _buildLoadingDots(),
          const SizedBox(height: 16),
          const Text(
            'Initializing AI Interview...',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: slateText,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingDots() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(3, (index) {
        return AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            // Offset the animation for a "wave" effect
            final delay = index * 0.2;
            final normalizedTime = (_controller.value - delay + 1.0) % 1.0;

            // Calculate opacity based on sine wave for smoothness
            final scale = (0.5 + 0.5 * (1 - (normalizedTime - 0.5).abs() * 2));

            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 5),
              width: 10,
              height: 10,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                // Using Cozy Blue for the dots to complement the Green icon
                color:
                    cozyBlue.withOpacitySafe(scale.clamp(0.2, 1.0).toDouble()),
              ),
            );
          },
        );
      }),
    );
  }
}
