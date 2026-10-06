import 'package:flutter/material.dart';
import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';

class AttachmentModel {
  final String id;
  final String fileName;
  final String filePath;
  final String fileType;
  final int fileSize;

  AttachmentModel({
    required this.id,
    required this.fileName,
    required this.filePath,
    required this.fileType,
    required this.fileSize,
  });

  factory AttachmentModel.fromJson(Map<String, dynamic> json) {
    return AttachmentModel(
      id: json["id"] ?? "",
      fileName: json["file_name"] ?? "",
      filePath: json["file_path"] ?? "",
      fileType: json["file_type"] ?? "",
      fileSize: json["file_size"] ?? 0,
    );
  }
}

class ReviewModel {
  final String id;
  final int score;
  final String? feedbackText;
  final String decision;
  final String reviewedAt;
  final String? reviewerName;

  ReviewModel({
    required this.id,
    required this.score,
    this.feedbackText,
    required this.decision,
    required this.reviewedAt,
    this.reviewerName,
  });

  factory ReviewModel.fromJson(Map<String, dynamic> json) {
    return ReviewModel(
      id: json["id"] ?? "",
      score: json["score"] ?? 0,
      feedbackText: json["feedback_text"],
      decision: json["decision"] ?? "APPROVED",
      reviewedAt: json["reviewed_at"] ?? "",
      reviewerName: json["reviewer"]?["full_name"],
    );
  }
}

class SubmissionModel {
  final String id;
  final String assignmentId;
  final String studentId;
  final String? studentName;
  final String? studentEmail;
  final String? answerText;
  final String status;
  final bool isLate;
  final String submittedAt;
  final List<AttachmentModel> attachments;
  final List<ReviewModel> reviews;
  final int? latestScore;
  final String? latestFeedback;

  SubmissionModel({
    required this.id,
    required this.assignmentId,
    required this.studentId,
    this.studentName,
    this.studentEmail,
    this.answerText,
    required this.status,
    this.isLate = false,
    required this.submittedAt,
    this.attachments = const [],
    this.reviews = const [],
    this.latestScore,
    this.latestFeedback,
  });

  factory SubmissionModel.fromJson(Map<String, dynamic> json) {
    final st = json["student"] ?? {};
    var rawAtts = json["attachments"] as List? ?? [];
    var rawRevs = json["reviews"] as List? ?? [];

    return SubmissionModel(
      id: json["id"] ?? "",
      assignmentId: json["assignment_id"] ?? "",
      studentId: json["student_id"] ?? "",
      studentName: st["full_name"],
      studentEmail: st["email"],
      answerText: json["answer_text"],
      status: json["status"] ?? "SUBMITTED",
      isLate: json["is_late"] ?? false,
      submittedAt: json["submitted_at"] ?? "",
      attachments: rawAtts.map((a) => AttachmentModel.fromJson(a)).toList(),
      reviews: rawRevs.map((r) => ReviewModel.fromJson(r)).toList(),
      latestScore: json["latest_score"],
      latestFeedback: json["latest_feedback"],
    );
  }
}

class AssignmentModel {
  final String id;
  final String title;
  final String description;
  final String? instructions;
  final String teacherId;
  final String? teacherName;
  final String? groupId;
  final String? groupName;
  final String deadline;
  final String priority;
  final int maxScore;
  final String status;
  final int totalSubmitted;
  final bool isSubmittedByMe;
  final String? mySubmissionStatus;
  final int? myScore;
  final bool isOverdue;
  final List<AttachmentModel> attachments;

  AssignmentModel({
    required this.id,
    required this.title,
    required this.description,
    this.instructions,
    required this.teacherId,
    this.teacherName,
    this.groupId,
    this.groupName,
    required this.deadline,
    required this.priority,
    required this.maxScore,
    required this.status,
    this.totalSubmitted = 0,
    this.isSubmittedByMe = false,
    this.mySubmissionStatus,
    this.myScore,
    this.isOverdue = false,
    this.attachments = const [],
  });

  factory AssignmentModel.fromJson(Map<String, dynamic> json) {
    var rawAtts = json["attachments"] as List? ?? [];
    return AssignmentModel(
      id: json["id"] ?? "",
      title: json["title"] ?? "",
      description: json["description"] ?? "",
      instructions: json["instructions"],
      teacherId: json["teacher_id"] ?? "",
      teacherName: json["teacher"]?["full_name"],
      groupId: json["group_id"],
      groupName: json["group_name"],
      deadline: json["deadline"] ?? "",
      priority: json["priority"] ?? "MEDIUM",
      maxScore: json["max_score"] ?? 100,
      status: json["status"] ?? "PUBLISHED",
      totalSubmitted: json["total_submitted"] ?? 0,
      isSubmittedByMe: json["is_submitted_by_me"] ?? false,
      mySubmissionStatus: json["my_submission_status"],
      myScore: json["my_score"],
      isOverdue: json["is_overdue"] ?? false,
      attachments: rawAtts.map((a) => AttachmentModel.fromJson(a)).toList(),
    );
  }
}

class AssignmentProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  List<AssignmentModel> _assignments = [];
  AssignmentModel? _selectedAssignment;
  List<SubmissionModel> _assignmentSubmissions = [];
  SubmissionModel? _selectedSubmission;
  bool _isLoading = false;
  String? _errorMessage;

  List<AssignmentModel> get assignments => _assignments;
  AssignmentModel? get selectedAssignment => _selectedAssignment;
  List<SubmissionModel> get assignmentSubmissions => _assignmentSubmissions;
  SubmissionModel? get selectedSubmission => _selectedSubmission;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchAssignments({
    String? groupId,
    String? filterStatus,
    String? search,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{};
      if (groupId != null) queryParams["group_id"] = groupId;
      if (filterStatus != null) queryParams["filter_status"] = filterStatus;
      if (search != null && search.isNotEmpty) queryParams["search"] = search;

      final res = await _api.dio.get(ApiConstants.assignments, queryParameters: queryParams);
      if (res.statusCode == 200) {
        final List list = res.data;
        _assignments = list.map((a) => AssignmentModel.fromJson(a)).toList();
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchAssignmentDetail(String id) async {
    _isLoading = true;
    notifyListeners();

    try {
      final res = await _api.dio.get("${ApiConstants.assignments}/$id");
      if (res.statusCode == 200) {
        _selectedAssignment = AssignmentModel.fromJson(res.data);
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> createAssignment({
    required String title,
    required String description,
    String? instructions,
    String? groupId,
    required DateTime deadline,
    required String priority,
    required int maxScore,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        ApiConstants.assignments,
        data: {
          "title": title.trim(),
          "description": description.trim(),
          "instructions": instructions?.trim(),
          "group_id": groupId,
          "deadline": deadline.toIso8601String(),
          "priority": priority,
          "max_score": maxScore,
          "status": "PUBLISHED",
        },
      );
      if (res.statusCode == 201) {
        await fetchAssignments();
        return true;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }

  Future<bool> submitTask({
    required String assignmentId,
    required String answerText,
    List<Map<String, dynamic>> attachments = const [],
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        "${ApiConstants.assignments}/$assignmentId/submit",
        data: {
          "answer_text": answerText.trim(),
          "attachments": attachments,
        },
      );
      if (res.statusCode == 201) {
        await fetchAssignmentDetail(assignmentId);
        await fetchAssignments();
        return true;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }

  Future<void> fetchSubmissionsForAssignment(String assignmentId) async {
    _isLoading = true;
    notifyListeners();

    try {
      final res = await _api.dio.get("${ApiConstants.assignments}/$assignmentId/submissions");
      if (res.statusCode == 200) {
        final List list = res.data;
        _assignmentSubmissions = list.map((s) => SubmissionModel.fromJson(s)).toList();
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> gradeSubmission({
    required String submissionId,
    required int score,
    String? feedback,
    String decision = "APPROVED",
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        "${ApiConstants.submissions}/$submissionId/review",
        data: {
          "score": score,
          "feedback_text": feedback?.trim(),
          "decision": decision,
        },
      );
      if (res.statusCode == 200) {
        if (_selectedAssignment != null) {
          await fetchSubmissionsForAssignment(_selectedAssignment!.id);
        }
        return true;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
    return false;
  }
}
