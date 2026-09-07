import 'package:flutter/material.dart';
import '../../core/storage/local_export_service.dart';
import '../../core/storage/local_storage_service.dart';

class StandaloneProvider extends ChangeNotifier {
  final LocalStorageService _storage = LocalStorageService();

  List<LocalGroup> _groups = [];
  List<LocalTask> _tasks = [];
  List<LocalRecord> _records = [];
  bool _isLoading = false;
  String? _selectedGroupId;

  List<LocalGroup> get groups => _groups;
  List<LocalTask> get tasks => _tasks;
  List<LocalRecord> get records => _records;
  bool get isLoading => _isLoading;
  String? get selectedGroupId => _selectedGroupId;

  LocalGroup? get currentGroup =>
      _groups.where((g) => g.id == _selectedGroupId).firstOrNull ?? (_groups.isNotEmpty ? _groups.first : null);

  List<LocalTask> get currentGroupTasks {
    if (_selectedGroupId == null) return _tasks;
    return _tasks.where((t) => t.groupId == _selectedGroupId).toList();
  }

  // Live Metrics
  int get totalStudentsCount => _groups.fold(0, (sum, g) => sum + g.students.length);
  int get totalTasksCount => _tasks.length;
  int get totalCompletedRecordsCount => _records.where((r) => r.isDone).length;

  double get overallCompletionRate {
    final possible = _groups.fold(0, (sum, g) {
      final grpTasks = _tasks.where((t) => t.groupId == g.id).length;
      return sum + (g.students.length * grpTasks);
    });
    if (possible == 0) return 0.0;
    return ((totalCompletedRecordsCount / possible) * 100).clamp(0, 100).toDouble();
  }

  /// Faqat berilgan guruh bo'yicha o'zlashtirish foizi. Bosh sahifada
  /// joriy guruh tanlanganida shu ko'rsatiladi — barcha guruhlar aralashib
  /// ketmasligi uchun.
  double completionRateForGroup(String groupId) {
    final grp = _groups.where((g) => g.id == groupId).firstOrNull;
    if (grp == null || grp.students.isEmpty) return 0.0;
    final grpTasks = _tasks.where((t) => t.groupId == groupId).toList();
    final possible = grp.students.length * grpTasks.length;
    if (possible == 0) return 0.0;
    final done = grpTasks.fold<int>(0, (sum, t) {
      return sum + grp.students.where((s) {
        final r = getRecord(t.id, s.id);
        return r != null && r.isDone;
      }).length;
    });
    return ((done / possible) * 100).clamp(0, 100).toDouble();
  }

  Future<void> init() async {
    _isLoading = true;
    notifyListeners();

    await _storage.initSeedIfEmpty();
    _groups = await _storage.loadGroups();
    _tasks = await _storage.loadTasks();
    _records = await _storage.loadRecords();

    if (_groups.isNotEmpty && _selectedGroupId == null) {
      _selectedGroupId = _groups.first.id;
    }

    _isLoading = false;
    notifyListeners();
  }

  void selectGroup(String groupId) {
    _selectedGroupId = groupId;
    notifyListeners();
  }

  // Group Operations
  Future<void> addGroup(String name, String? desc) async {
    final newGroup = LocalGroup(
      id: 'grp-${DateTime.now().millisecondsSinceEpoch}',
      name: name.trim(),
      description: desc?.trim(),
      students: [],
    );
    _groups.add(newGroup);
    _selectedGroupId = newGroup.id;
    await _storage.saveGroups(_groups);
    notifyListeners();
  }

  Future<void> deleteGroup(String groupId) async {
    final removedTaskIds = _tasks.where((t) => t.groupId == groupId).map((t) => t.id).toSet();
    final removedStudentIds =
        _groups.where((g) => g.id == groupId).expand((g) => g.students).map((s) => s.id).toSet();

    _groups.removeWhere((g) => g.id == groupId);
    _tasks.removeWhere((t) => t.groupId == groupId);
    // Guruh bilan birga uning vazifa/talaba yozuvlarini ham tozalash —
    // aks holda qolgan guruhlarning o'zlashtirish foizi buzilib qoladi.
    _records.removeWhere((r) => removedTaskIds.contains(r.taskId) || removedStudentIds.contains(r.studentId));

    if (_selectedGroupId == groupId) {
      _selectedGroupId = _groups.isNotEmpty ? _groups.first.id : null;
    }
    await _storage.saveGroups(_groups);
    await _storage.saveTasks(_tasks);
    await _storage.saveRecords(_records);
    notifyListeners();
  }

  // Student Operations
  Future<void> addStudent(String groupId, String name, String? phone) async {
    final grpIndex = _groups.indexWhere((g) => g.id == groupId);
    if (grpIndex != -1) {
      final st = LocalStudent(
        id: 'st-${DateTime.now().millisecondsSinceEpoch}',
        name: name.trim(),
        phone: phone?.trim(),
      );
      final updatedStudents = List<LocalStudent>.from(_groups[grpIndex].students)..add(st);
      _groups[grpIndex] = LocalGroup(
        id: _groups[grpIndex].id,
        name: _groups[grpIndex].name,
        description: _groups[grpIndex].description,
        students: updatedStudents,
      );
      await _storage.saveGroups(_groups);
      notifyListeners();
    }
  }

  Future<void> updateStudent(String groupId, String studentId, String name, String? phone) async {
    final grpIndex = _groups.indexWhere((g) => g.id == groupId);
    if (grpIndex == -1) return;
    final updatedStudents = _groups[grpIndex].students.map((s) {
      if (s.id != studentId) return s;
      return LocalStudent(id: s.id, name: name.trim(), phone: phone?.trim(), email: s.email);
    }).toList();
    _groups[grpIndex] = LocalGroup(
      id: _groups[grpIndex].id,
      name: _groups[grpIndex].name,
      description: _groups[grpIndex].description,
      students: updatedStudents,
    );
    await _storage.saveGroups(_groups);
    notifyListeners();
  }

  Future<void> deleteStudent(String groupId, String studentId) async {
    final grpIndex = _groups.indexWhere((g) => g.id == groupId);
    if (grpIndex != -1) {
      final updatedStudents = List<LocalStudent>.from(_groups[grpIndex].students)
        ..removeWhere((s) => s.id == studentId);
      _groups[grpIndex] = LocalGroup(
        id: _groups[grpIndex].id,
        name: _groups[grpIndex].name,
        description: _groups[grpIndex].description,
        students: updatedStudents,
      );
      _records.removeWhere((r) => r.studentId == studentId);
      await _storage.saveGroups(_groups);
      await _storage.saveRecords(_records);
      notifyListeners();
    }
  }

  // Task Operations
  Future<void> addTask({
    required String groupId,
    required String title,
    required String description,
    int maxScore = 100,
    required DateTime deadline,
    String priority = 'MEDIUM',
  }) async {
    final task = LocalTask(
      id: 'tsk-${DateTime.now().millisecondsSinceEpoch}',
      groupId: groupId,
      title: title.trim(),
      description: description.trim(),
      maxScore: maxScore,
      deadline: deadline.toIso8601String(),
      priority: priority,
    );
    _tasks.insert(0, task);
    await _storage.saveTasks(_tasks);
    notifyListeners();
  }

  Future<void> updateTask({
    required String taskId,
    required String title,
    required String description,
    required int maxScore,
    required DateTime deadline,
    required String priority,
  }) async {
    final idx = _tasks.indexWhere((t) => t.id == taskId);
    if (idx == -1) return;
    _tasks[idx] = LocalTask(
      id: _tasks[idx].id,
      groupId: _tasks[idx].groupId,
      title: title.trim(),
      description: description.trim(),
      maxScore: maxScore,
      deadline: deadline.toIso8601String(),
      priority: priority,
    );
    await _storage.saveTasks(_tasks);
    notifyListeners();
  }

  Future<void> deleteTask(String taskId) async {
    _tasks.removeWhere((t) => t.id == taskId);
    _records.removeWhere((r) => r.taskId == taskId);
    await _storage.saveTasks(_tasks);
    await _storage.saveRecords(_records);
    notifyListeners();
  }

  // Rapid Marking in Classroom
  LocalRecord? getRecord(String taskId, String studentId) {
    return _records.where((r) => r.taskId == taskId && r.studentId == studentId).firstOrNull;
  }

  Future<void> toggleRecord({
    required String taskId,
    required String studentId,
    required bool isDone,
    int score = 100,
    String? feedback,
  }) async {
    final idx = _records.indexWhere((r) => r.taskId == taskId && r.studentId == studentId);
    final rec = LocalRecord(
      taskId: taskId,
      studentId: studentId,
      isDone: isDone,
      score: isDone ? score : 0,
      feedback: feedback,
      markedAt: DateTime.now().toIso8601String(),
    );

    if (idx != -1) {
      _records[idx] = rec;
    } else {
      _records.add(rec);
    }

    await _storage.saveRecords(_records);
    notifyListeners();
  }

  Future<void> batchMarkGroupTask(String taskId, String groupId, bool isDone) async {
    final grp = _groups.where((g) => g.id == groupId).firstOrNull;
    final task = _tasks.where((t) => t.id == taskId).firstOrNull;
    if (grp == null) return;

    for (final st in grp.students) {
      final idx = _records.indexWhere((r) => r.taskId == taskId && r.studentId == st.id);
      // Avvalgi izoh va (bajarilgan bo'lsa) bahoni saqlab qolamiz — ommaviy
      // belgilash o'qituvchi allaqachon yozgan izohlarni o'chirib
      // yubormasligi uchun.
      final existing = idx != -1 ? _records[idx] : null;
      final rec = LocalRecord(
        taskId: taskId,
        studentId: st.id,
        isDone: isDone,
        score: isDone ? ((existing != null && existing.isDone) ? existing.score : (task?.maxScore ?? 100)) : 0,
        feedback: existing?.feedback,
        markedAt: DateTime.now().toIso8601String(),
      );
      if (idx != -1) {
        _records[idx] = rec;
      } else {
        _records.add(rec);
      }
    }

    await _storage.saveRecords(_records);
    notifyListeners();
  }

  // Export
  Future<String?> exportPdf(String groupId) async {
    final grp = _groups.where((g) => g.id == groupId).firstOrNull;
    if (grp == null) return null;
    final grpTasks = _tasks.where((t) => t.groupId == groupId).toList();
    return await LocalExportService.exportGroupPdf(group: grp, tasks: grpTasks, records: _records);
  }

  Future<String?> exportExcel(String groupId) async {
    final grp = _groups.where((g) => g.id == groupId).firstOrNull;
    if (grp == null) return null;
    final grpTasks = _tasks.where((t) => t.groupId == groupId).toList();
    return await LocalExportService.exportGroupExcel(group: grp, tasks: grpTasks, records: _records);
  }
}
