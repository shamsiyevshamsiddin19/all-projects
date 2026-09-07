import 'package:flutter/material.dart';
import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';

class GroupMemberModel {
  final String id;
  final String studentId;
  final String fullName;
  final String email;
  final String joinedAt;

  GroupMemberModel({
    required this.id,
    required this.studentId,
    required this.fullName,
    required this.email,
    required this.joinedAt,
  });

  factory GroupMemberModel.fromJson(Map<String, dynamic> json) {
    final st = json["student"] ?? {};
    return GroupMemberModel(
      id: json["id"] ?? "",
      studentId: st["id"] ?? "",
      fullName: st["full_name"] ?? "",
      email: st["email"] ?? "",
      joinedAt: json["joined_at"] ?? "",
    );
  }
}

class GroupModel {
  final String id;
  final String name;
  final String? description;
  final String inviteCode;
  final String teacherId;
  final int totalStudents;
  final int totalAssignments;
  final List<GroupMemberModel> members;

  GroupModel({
    required this.id,
    required this.name,
    this.description,
    required this.inviteCode,
    required this.teacherId,
    this.totalStudents = 0,
    this.totalAssignments = 0,
    this.members = const [],
  });

  factory GroupModel.fromJson(Map<String, dynamic> json) {
    var rawMembers = json["members"] as List? ?? [];
    return GroupModel(
      id: json["id"] ?? "",
      name: json["name"] ?? "",
      description: json["description"],
      inviteCode: json["invite_code"] ?? "",
      teacherId: json["teacher_id"] ?? "",
      totalStudents: json["total_students"] ?? 0,
      totalAssignments: json["total_assignments"] ?? 0,
      members: rawMembers.map((m) => GroupMemberModel.fromJson(m)).toList(),
    );
  }
}

class GroupProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  List<GroupModel> _groups = [];
  GroupModel? _selectedGroup;
  bool _isLoading = false;
  String? _errorMessage;

  List<GroupModel> get groups => _groups;
  GroupModel? get selectedGroup => _selectedGroup;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchGroups() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.get(ApiConstants.groups);
      if (res.statusCode == 200) {
        final List list = res.data;
        _groups = list.map((g) => GroupModel.fromJson(g)).toList();
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> createGroup(String name, String? description) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        ApiConstants.groups,
        data: {"name": name.trim(), "description": description?.trim()},
      );
      if (res.statusCode == 201) {
        await fetchGroups();
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

  Future<bool> joinGroup(String inviteCode) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        ApiConstants.groupsJoin,
        data: {"invite_code": inviteCode.trim().toUpperCase()},
      );
      if (res.statusCode == 200) {
        await fetchGroups();
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

  Future<void> fetchGroupDetail(String groupId) async {
    _isLoading = true;
    notifyListeners();

    try {
      final res = await _api.dio.get("${ApiConstants.groups}/$groupId");
      if (res.statusCode == 200) {
        _selectedGroup = GroupModel.fromJson(res.data);
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> deleteGroup(String groupId) async {
    try {
      final res = await _api.dio.delete("${ApiConstants.groups}/$groupId");
      if (res.statusCode == 200) {
        _groups.removeWhere((g) => g.id == groupId);
        notifyListeners();
        return true;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    }
    return false;
  }
}
