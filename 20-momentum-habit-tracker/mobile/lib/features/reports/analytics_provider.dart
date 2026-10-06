import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';

class ActivityPointModel {
  final String label;
  final int value;

  ActivityPointModel({required this.label, required this.value});

  factory ActivityPointModel.fromJson(Map<String, dynamic> json) {
    return ActivityPointModel(
      label: json["label"] ?? "",
      value: json["value"] ?? 0,
    );
  }
}

class GroupPerformanceModel {
  final String groupId;
  final String groupName;
  final int totalStudents;
  final double completionRate;
  final double averageScore;

  GroupPerformanceModel({
    required this.groupId,
    required this.groupName,
    required this.totalStudents,
    required this.completionRate,
    required this.averageScore,
  });

  factory GroupPerformanceModel.fromJson(Map<String, dynamic> json) {
    return GroupPerformanceModel(
      groupId: json["group_id"] ?? "",
      groupName: json["group_name"] ?? "",
      totalStudents: json["total_students"] ?? 0,
      completionRate: (json["completion_rate"] as num?)?.toDouble() ?? 0.0,
      averageScore: (json["average_score"] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class TopStudentModel {
  final String studentId;
  final String studentName;
  final String? avatarUrl;
  final int completedTasks;
  final double averageScore;

  TopStudentModel({
    required this.studentId,
    required this.studentName,
    this.avatarUrl,
    required this.completedTasks,
    required this.averageScore,
  });

  factory TopStudentModel.fromJson(Map<String, dynamic> json) {
    return TopStudentModel(
      studentId: json["student_id"] ?? "",
      studentName: json["student_name"] ?? "",
      avatarUrl: json["avatar_url"],
      completedTasks: json["completed_tasks"] ?? 0,
      averageScore: (json["average_score"] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class DashboardStatsModel {
  final int totalStudents;
  final int totalGroups;
  final int activeAssignments;
  final int completedAssignments;
  final int pendingReviews;
  final int lateSubmissions;
  final double averageScore;
  final double completionRate;
  final List<ActivityPointModel> weeklyActivity;
  final List<GroupPerformanceModel> groupPerformances;
  final List<TopStudentModel> topStudents;

  // Student specific stats
  final int activeTasks;
  final int completedTasks;
  final int overdueTasks;

  DashboardStatsModel({
    this.totalStudents = 0,
    this.totalGroups = 0,
    this.activeAssignments = 0,
    this.completedAssignments = 0,
    this.pendingReviews = 0,
    this.lateSubmissions = 0,
    this.averageScore = 0.0,
    this.completionRate = 0.0,
    this.weeklyActivity = const [],
    this.groupPerformances = const [],
    this.topStudents = const [],
    this.activeTasks = 0,
    this.completedTasks = 0,
    this.overdueTasks = 0,
  });

  factory DashboardStatsModel.fromJson(Map<String, dynamic> json) {
    var rawAct = (json["weekly_activity"] ?? json["weekly_progress"]) as List? ?? [];
    var rawGroups = json["group_performances"] as List? ?? [];
    var rawTops = json["top_students"] as List? ?? [];

    return DashboardStatsModel(
      totalStudents: json["total_students"] ?? 0,
      totalGroups: json["total_groups"] ?? 0,
      activeAssignments: json["active_assignments"] ?? 0,
      completedAssignments: json["completed_assignments"] ?? 0,
      pendingReviews: json["pending_reviews"] ?? 0,
      lateSubmissions: json["late_submissions"] ?? 0,
      averageScore: (json["average_score"] as num?)?.toDouble() ?? 0.0,
      completionRate: (json["completion_rate"] as num?)?.toDouble() ?? 0.0,
      weeklyActivity: rawAct.map((a) => ActivityPointModel.fromJson(a)).toList(),
      groupPerformances: rawGroups.map((g) => GroupPerformanceModel.fromJson(g)).toList(),
      topStudents: rawTops.map((t) => TopStudentModel.fromJson(t)).toList(),
      activeTasks: json["active_tasks"] ?? 0,
      completedTasks: json["completed_tasks"] ?? 0,
      overdueTasks: json["overdue_tasks"] ?? 0,
    );
  }
}

class AnalyticsProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  DashboardStatsModel? _stats;
  bool _isLoading = false;
  bool _isExporting = false;
  String? _errorMessage;

  DashboardStatsModel? get stats => _stats;
  bool get isLoading => _isLoading;
  bool get isExporting => _isExporting;
  String? get errorMessage => _errorMessage;

  Future<void> fetchDashboardStats() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.get(ApiConstants.analyticsDashboard);
      if (res.statusCode == 200) {
        _stats = DashboardStatsModel.fromJson(res.data);
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<String?> exportReportPdf({String? groupId}) async {
    _isExporting = true;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (groupId != null) queryParams["group_id"] = groupId;

      final dir = await getTemporaryDirectory();
      final savePath = "${dir.path}/Tracker_Report_${DateTime.now().millisecondsSinceEpoch}.pdf";

      final res = await _api.dio.download(
        ApiConstants.exportPdf,
        savePath,
        queryParameters: queryParams,
      );

      if (res.statusCode == 200) {
        await OpenFilex.open(savePath);
        return savePath;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isExporting = false;
      notifyListeners();
    }
    return null;
  }

  Future<String?> exportReportExcel({String? groupId}) async {
    _isExporting = true;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (groupId != null) queryParams["group_id"] = groupId;

      final dir = await getTemporaryDirectory();
      final savePath = "${dir.path}/Tracker_Report_${DateTime.now().millisecondsSinceEpoch}.xlsx";

      final res = await _api.dio.download(
        ApiConstants.exportExcel,
        savePath,
        queryParameters: queryParams,
      );

      if (res.statusCode == 200) {
        await OpenFilex.open(savePath);
        return savePath;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isExporting = false;
      notifyListeners();
    }
    return null;
  }
}
