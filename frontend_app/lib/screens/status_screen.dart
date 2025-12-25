import 'package:flutter/material.dart';
import '../widgets/status_card.dart';
import '../widgets/animated_wave.dart';

class StatusScreen extends StatelessWidget {
  final Map<String, dynamic> status;

  const StatusScreen({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    // Extracting data with safe defaults
    final String stage = status['stage']?.toString() ?? 'Introduction';
    final String question =
        status['question']?.toString() ?? 'Waiting for the next question...';
    final int score = int.tryParse(status['score']?.toString() ?? '0') ?? 0;
    final double avgScore =
        double.tryParse(status['average_score']?.toString() ?? '0.0') ?? 0.0;
    final bool isCompleted = status['completed'] == true;

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA), // Surface White
      appBar: AppBar(
        title: const Text(
          "Interview Status",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          // 1. Background decorative wave at the bottom
          const Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            height: 200,
            child: AnimatedWave(),
          ),

          // 2. Main Content
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),

                  // Title Header
                  const Text(
                    "Current Session",
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "Here is the real-time analysis of your interview progress.",
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                      height: 1.5,
                    ),
                  ),

                  const SizedBox(height: 30),

                  // The polished Status Card
                  StatusCard(
                    stage: stage,
                    question: question,
                    score: score,
                    avgScore: avgScore,
                    completed: isCompleted,
                  ),

                  const Spacer(),

                  // Action Button (Contextual)
                  Center(
                    child: isCompleted
                        ? ElevatedButton.icon(
                            onPressed: () {
                              // Navigate back or to results
                              Navigator.pop(context);
                            },
                            icon: const Icon(Icons.check),
                            label: const Text("Finish & View Report"),
                            style: ElevatedButton.styleFrom(
                              minimumSize: const Size(double.infinity, 50),
                            ),
                          )
                        : OutlinedButton.icon(
                            onPressed: () {
                              // Refresh logic could go here
                            },
                            icon: const Icon(Icons.refresh_rounded),
                            label: const Text("Refresh Status"),
                            style: OutlinedButton.styleFrom(
                              foregroundColor:
                                  const Color(0xFF1A5E41), // Manchester Green
                              side: const BorderSide(color: Color(0xFF1A5E41)),
                              minimumSize: const Size(double.infinity, 50),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
