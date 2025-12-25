import 'dart:async';
import 'package:flutter/material.dart';
import '../utils/helpers.dart';
import '../services/interview_service.dart';
import '../widgets/loading_indicator.dart';
import '../widgets/status_card.dart';
import '../widgets/animated_wave.dart';

class InterviewScreen extends StatefulWidget {
  const InterviewScreen({super.key});

  @override
  State<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends State<InterviewScreen> {
  final InterviewService _service = InterviewService();
  Map<String, dynamic>? statusData;
  Timer? poller;
  bool interviewStarted = false;
  bool completed = false;

  // Theme Colors
  static const Color manchesterGreen = Color(0xFF1A5E41);
  static const Color cozyBlue = Color(0xFF5D8AA8);
  static const Color surfaceWhite = Color(0xFFF8F9FA);

  @override
  void initState() {
    super.initState();
    _startInterview();
  }

  Future<void> _startInterview() async {
    try {
      await _service.startInterview();
      if (mounted) {
        setState(() => interviewStarted = true);
        _startPolling();
      }
    } catch (e) {
      // Handle connection errors gracefully
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Failed to start interview: $e")),
        );
      }
    }
  }

  void _startPolling() {
    poller = Timer.periodic(const Duration(seconds: 2), (_) async {
      try {
        final data = await _service.getStatus();

        if (mounted) {
          setState(() {
            statusData = data;
            completed = data["completed"] == true;
          });

          if (completed) {
            poller?.cancel();
          }
        }
      } catch (e) {
        debugPrint("Polling error: $e");
      }
    });
  }

  @override
  void dispose() {
    poller?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: surfaceWhite,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: manchesterGreen),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text(
          "Live Session",
          style: TextStyle(color: manchesterGreen, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          // 1. Background Animation
          const Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            height: 250,
            child: AnimatedWave(),
          ),

          // 2. Main Content
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 10, 20, 20),
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 500),
                child: statusData == null
                    ? _buildLoadingState()
                    : _buildActiveState(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingState() {
    return const Center(
      key: ValueKey('loading'),
      child: LoadingIndicator(),
    );
  }

  Widget _buildActiveState() {
    // Safely extract data
    final String stage = statusData!["stage"]?.toString() ?? "Initializing";
    final String question =
        statusData!["question"]?.toString() ?? "Preparing your question...";
    final int score =
        int.tryParse(statusData!["last_score"]?.toString() ?? "0") ?? 0;
    final double avgScore =
        double.tryParse(statusData!["avg_score"]?.toString() ?? "0.0") ?? 0.0;

    return SingleChildScrollView(
      key: const ValueKey('loaded'),
      physics: const BouncingScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 10),

          // Context Header
          Text(
            completed ? "Session Complete" : "AI is listening...",
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: completed ? manchesterGreen : cozyBlue,
              letterSpacing: 0.5,
            ),
          ),

          const SizedBox(height: 20),

          // Candidate name if available
          if ((statusData!["name"] ?? "").toString().isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12.0),
              child: Row(
                children: [
                  const Icon(Icons.person, color: manchesterGreen),
                  const SizedBox(width: 8),
                  Text(
                    statusData!["name"].toString(),
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                ],
              ),
            ),

          // Main Data Card
          StatusCard(
            stage: stage,
            question: question,
            score: score,
            avgScore: avgScore,
            completed: completed,
          ),

          const SizedBox(height: 40),

          // Result Section (Only visible when completed)
          if (completed)
            Container(
              padding: const EdgeInsets.all(24),
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: manchesterGreen.withOpacitySafe(0.1),
                    blurRadius: 20,
                    offset: const Offset(0, 10),
                  ),
                ],
              ),
              child: Column(
                children: [
                  const Icon(Icons.emoji_events_rounded,
                      size: 48, color: manchesterGreen),
                  const SizedBox(height: 16),
                  const Text(
                    "Great Job!",
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    "You achieved an average score of $avgScore. Keep practicing to improve your technical vocabulary.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 15,
                      color: Colors.grey[600],
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () => Navigator.of(context).pop(),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: manchesterGreen,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(double.infinity, 50),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      elevation: 0,
                    ),
                    child: const Text("Return to Home"),
                  ),
                ],
              ),
            )
          else
            // Hints/Tips while waiting (optional filler)
            Center(
              child: Padding(
                padding: const EdgeInsets.only(top: 40.0),
                child: Text(
                  "Tip: Speak clearly and take your time.",
                  style: TextStyle(
                    color: Colors.grey.withOpacitySafe(0.5),
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
