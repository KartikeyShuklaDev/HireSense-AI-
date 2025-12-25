import 'dart:convert';
import 'package:http/http.dart';
import '../constants/api_constants.dart';
import 'api_client.dart';

class InterviewService {
  final ApiClient _client = ApiClient();

  /// Initiates a new interview session.
  /// Returns a map containing the session ID and initial context.
  Future<Map<String, dynamic>> startInterview() async {
    final Response res = await _client.post(ApiConstants.startInterview);
    return jsonDecode(res.body);
  }

  /// Fetches the real-time status of the current interview.
  /// Includes current question, score, and stage progress.
  Future<Map<String, dynamic>> getStatus() async {
    final Response res = await _client.get(ApiConstants.statusInterview);
    return jsonDecode(res.body);
  }

  /// Ends the interview session and retrieves final feedback.
  Future<Map<String, dynamic>> endInterview() async {
    final Response res = await _client.post(ApiConstants.endInterview);
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> getHistory({int limit = 20}) async {
    final Response res = await _client.get(
      "${ApiConstants.historyInterview}?limit=$limit",
    );
    return jsonDecode(res.body);
  }
}
