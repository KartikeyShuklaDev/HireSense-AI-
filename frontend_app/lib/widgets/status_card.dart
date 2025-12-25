import 'package:flutter/material.dart';
import '../utils/helpers.dart';

class StatusCard extends StatelessWidget {
  final String stage;
  final String question;
  final int score;
  final double avgScore;
  final bool completed;

  const StatusCard({
    super.key,
    required this.stage,
    required this.question,
    required this.score,
    required this.avgScore,
    required this.completed,
  });

  @override
  Widget build(BuildContext context) {
    // Define theme colors locally for this widget to ensure consistency
    const manchesterGreen = Color(0xFF1A5E41);
    const cozyBlue = Color(0xFF5D8AA8);
    const surfaceColor = Colors.white;

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
      decoration: BoxDecoration(
        color: surfaceColor,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1E293B).withOpacitySafe(0.08),
            offset: const Offset(0, 4),
            blurRadius: 12,
            spreadRadius: 0,
          ),
        ],
        border: Border.all(
          color: completed
              ? manchesterGreen.withOpacitySafe(0.3)
              : Colors.transparent,
          width: 1.5,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // --- Header: Stage & Status Badge ---
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: cozyBlue.withOpacitySafe(0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    "Stage: $stage",
                    style: const TextStyle(
                      color: cozyBlue,
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                    ),
                  ),
                ),
                if (completed)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: manchesterGreen,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.check_circle, size: 14, color: Colors.white),
                        SizedBox(width: 4),
                        Text(
                          "Done",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),

            const SizedBox(height: 16),

            // --- Question Text ---
            Text(
              question,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Color(0xFF1E293B),
                height: 1.4,
              ),
            ),

            const SizedBox(height: 20),

            // --- Footer: Stats Grid ---
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF8F9FA), // Subtle grey bg
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  // Score Item
                  Expanded(
                    child: _buildStatItem(
                      label: "Your Score",
                      value: "$score",
                      color: manchesterGreen,
                      icon: Icons.stars_rounded,
                    ),
                  ),
                  // Divider
                  Container(
                    height: 40,
                    width: 1,
                    color: Colors.grey.withOpacitySafe(0.2),
                  ),
                  // Avg Item
                  Expanded(
                    child: _buildStatItem(
                      label: "Avg. Score",
                      value: avgScore.toStringAsFixed(1),
                      color: cozyBlue,
                      icon: Icons.analytics_outlined,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem({
    required String label,
    required String value,
    required Color color,
    required IconData icon,
  }) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 16, color: color.withOpacitySafe(0.7)),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
            color: color,
          ),
        ),
      ],
    );
  }
}
