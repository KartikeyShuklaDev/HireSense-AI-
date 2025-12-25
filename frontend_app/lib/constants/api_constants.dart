class ApiConstants {
  // Use your LAN IP so device/emulator can reach Flask server
  // For Android emulator: http://10.0.2.2:5000
  // For iOS simulator: http://127.0.0.1:5000
  // For physical device: http://192.168.29.186:5000
  // For Windows/Web on same machine: http://localhost:5000
  static const String baseUrl = "http://localhost:5000";

  static const String startInterview = "$baseUrl/api/interview/start";
  static const String statusInterview = "$baseUrl/api/interview/status";
  static const String endInterview = "$baseUrl/api/interview/end";
  static const String historyInterview = "$baseUrl/api/interview/history";
}
