import 'package:flutter/material.dart';
import 'dart:developer' as developer;
import '../services/interview_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final InterviewService _service = InterviewService();
  List<Map<String, dynamic>> items = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final res = await _service.getHistory(limit: 50);
      developer.log('History response: $res');

      // Safely extract items from response
      final itemsData = res['items'];
      late List<Map<String, dynamic>> list;

      if (itemsData is List) {
        list = itemsData
            .whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList();
      } else {
        list = [];
      }

      if (mounted) {
        setState(() {
          items = list;
          loading = false;
        });
      }
    } catch (e, stackTrace) {
      developer.log('Error loading history: $e', stackTrace: stackTrace);
      if (mounted) {
        setState(() => loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load history: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Interview History')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : items.isEmpty
              ? const Center(child: Text('No sessions yet'))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemBuilder: (context, i) {
                    final Map<String, dynamic> it = items[i];
                    final String name = it['name']?.toString() ?? 'Unknown';
                    final dynamic avg = it['avg_score'] ?? 0;
                    final String created = it['created_at']?.toString() ?? '';
                    return ListTile(
                      tileColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      title: Text(name,
                          style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: Text('Avg Score: $avg\nDate: $created'),
                      leading: const Icon(Icons.person_outline),
                    );
                  },
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemCount: items.length,
                ),
    );
  }
}
