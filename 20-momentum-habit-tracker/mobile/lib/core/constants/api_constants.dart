class ApiConstants {
  // Use localhost for Linux/macOS/Web, or 10.0.2.2 for Android emulator
  static const String defaultBaseUrl = "http://127.0.0.1:8000";
  
  static const String authRegister = "/api/v1/auth/register";
  static const String authLogin = "/api/v1/auth/login";
  static const String authRefresh = "/api/v1/auth/refresh";
  static const String authMe = "/api/v1/auth/me";
  
  static const String usersProfile = "/api/v1/users/profile";
  static const String usersStudents = "/api/v1/users/students";
  
  static const String groups = "/api/v1/groups";
  static const String groupsJoin = "/api/v1/groups/join";
  
  static const String assignments = "/api/v1/assignments";
  static const String submissions = "/api/v1/submissions";
  
  static const String analyticsDashboard = "/api/v1/analytics/dashboard";
  static const String exportPdf = "/api/v1/analytics/export/pdf";
  static const String exportExcel = "/api/v1/analytics/export/excel";
  
  static const String notifications = "/api/v1/notifications";
  static const String filesUpload = "/api/v1/files/upload";
}
