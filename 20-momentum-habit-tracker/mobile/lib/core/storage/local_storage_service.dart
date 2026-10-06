import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class LocalStudent {
  final String id;
  final String name;
  final String? phone;
  final String? email;

  LocalStudent({required this.id, required this.name, this.phone, this.email});

  factory LocalStudent.fromJson(Map<String, dynamic> json) => LocalStudent(
        id: json['id'] ?? '',
        name: json['name'] ?? '',
        phone: json['phone'],
        email: json['email'],
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'phone': phone,
        'email': email,
      };
}

class LocalGroup {
  final String id;
  final String name;
  final String? description;
  final List<LocalStudent> students;

  LocalGroup({
    required this.id,
    required this.name,
    this.description,
    this.students = const [],
  });

  factory LocalGroup.fromJson(Map<String, dynamic> json) {
    var rawSt = json['students'] as List? ?? [];
    return LocalGroup(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'],
      students: rawSt.map((s) => LocalStudent.fromJson(s)).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'description': description,
        'students': students.map((s) => s.toJson()).toList(),
      };
}

class LocalTask {
  final String id;
  final String groupId;
  final String title;
  final String description;
  final int maxScore;
  final String deadline;
  final String priority; // LOW, MEDIUM, HIGH, URGENT

  LocalTask({
    required this.id,
    required this.groupId,
    required this.title,
    required this.description,
    this.maxScore = 100,
    required this.deadline,
    this.priority = 'MEDIUM',
  });

  factory LocalTask.fromJson(Map<String, dynamic> json) => LocalTask(
        id: json['id'] ?? '',
        groupId: json['group_id'] ?? '',
        title: json['title'] ?? '',
        description: json['description'] ?? '',
        maxScore: json['max_score'] ?? 100,
        deadline: json['deadline'] ?? '',
        priority: json['priority'] ?? 'MEDIUM',
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'group_id': groupId,
        'title': title,
        'description': description,
        'max_score': maxScore,
        'deadline': deadline,
        'priority': priority,
      };
}

class LocalRecord {
  final String taskId;
  final String studentId;
  final bool isDone;
  final int score;
  final String? feedback;
  final String markedAt;

  LocalRecord({
    required this.taskId,
    required this.studentId,
    required this.isDone,
    required this.score,
    this.feedback,
    required this.markedAt,
  });

  factory LocalRecord.fromJson(Map<String, dynamic> json) => LocalRecord(
        taskId: json['task_id'] ?? '',
        studentId: json['student_id'] ?? '',
        isDone: json['is_done'] ?? false,
        score: json['score'] ?? 0,
        feedback: json['feedback'],
        markedAt: json['marked_at'] ?? '',
      );

  Map<String, dynamic> toJson() => {
        'task_id': taskId,
        'student_id': studentId,
        'is_done': isDone,
        'score': score,
        'feedback': feedback,
        'marked_at': markedAt,
      };
}

class LocalStorageService {
  static const _groupsKey = 'standalone_groups_v2';
  static const _tasksKey = 'standalone_tasks_v2';
  static const _recordsKey = 'standalone_records_v2';

  Future<void> initSeedIfEmpty() async {
    final prefs = await SharedPreferences.getInstance();
    if (!prefs.containsKey(_groupsKey)) {
      // Namuna ma'lumotlar — ilovani birinchi marta ochganda bo'sh ekran
      // ko'rinmasligi va tugmalar nimaga xizmat qilishi tushunarli bo'lishi
      // uchun. Fan/yo'nalishga bog'liq emas — dasturlash o'qituvchisi ham,
      // boshqa har qanday fan o'qituvchisi ham shu namunani ko'radi.
      final defaultGroups = [
        LocalGroup(
          id: 'grp-1',
          name: '1-guruh',
          description: 'Dushanba / Chorshanba / Juma 18:00',
          students: [
            LocalStudent(id: 'st-1', name: 'Azizbek Rahimov', phone: '+998 90 111 22 33'),
            LocalStudent(id: 'st-2', name: 'Jasur Toshmatov', phone: '+998 91 222 33 44'),
            LocalStudent(id: 'st-3', name: 'Madina Alimova', phone: '+998 93 333 44 55'),
            LocalStudent(id: 'st-4', name: 'Sardor Qobilov', phone: '+998 97 444 55 66'),
            LocalStudent(id: 'st-5', name: 'Laylo Karimova', phone: '+998 99 555 66 77'),
          ],
        ),
        LocalGroup(
          id: 'grp-2',
          name: '2-guruh',
          description: 'Seshanba / Payshanba / Shanba 15:00',
          students: [
            LocalStudent(id: 'st-6', name: 'Bobur Shokirov', phone: '+998 90 777 88 99'),
            LocalStudent(id: 'st-7', name: 'Nilufar Umarova', phone: '+998 91 888 99 00'),
            LocalStudent(id: 'st-8', name: 'Shohruh Nazarov', phone: '+998 93 999 00 11'),
          ],
        ),
      ];

      final defaultTasks = [
        LocalTask(
          id: 'tsk-1',
          groupId: 'grp-1',
          title: '1-Uy vazifasi',
          description: 'Darslikdagi topshiriqlarni bajarish',
          maxScore: 100,
          deadline: DateTime.now().add(const Duration(days: 2)).toIso8601String(),
          priority: 'HIGH',
        ),
        LocalTask(
          id: 'tsk-2',
          groupId: 'grp-1',
          title: '1-Nazorat ishi',
          description: "O'tilgan mavzular bo'yicha yozma nazorat",
          maxScore: 100,
          deadline: DateTime.now().add(const Duration(days: 5)).toIso8601String(),
          priority: 'URGENT',
        ),
        LocalTask(
          id: 'tsk-3',
          groupId: 'grp-2',
          title: '1-Amaliy topshiriq',
          description: "Mavzu bo'yicha amaliy mashg'ulot",
          maxScore: 100,
          deadline: DateTime.now().add(const Duration(days: 3)).toIso8601String(),
          priority: 'MEDIUM',
        ),
      ];

      final defaultRecords = [
        LocalRecord(
          taskId: 'tsk-1',
          studentId: 'st-1',
          isDone: true,
          score: 95,
          feedback: 'A\'lo bajarilgan!',
          markedAt: DateTime.now().toIso8601String(),
        ),
        LocalRecord(
          taskId: 'tsk-1',
          studentId: 'st-2',
          isDone: true,
          score: 85,
          feedback: 'Yaxshi, lekin ozroq shoshilgansiz',
          markedAt: DateTime.now().toIso8601String(),
        ),
        LocalRecord(
          taskId: 'tsk-1',
          studentId: 'st-3',
          isDone: false,
          score: 0,
          feedback: 'Darsga kelmadi',
          markedAt: DateTime.now().toIso8601String(),
        ),
      ];

      await saveGroups(defaultGroups);
      await saveTasks(defaultTasks);
      await saveRecords(defaultRecords);
    }
  }

  Future<List<LocalGroup>> loadGroups() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString(_groupsKey);
    if (str == null) return [];
    final List list = jsonDecode(str);
    return list.map((g) => LocalGroup.fromJson(g)).toList();
  }

  Future<void> saveGroups(List<LocalGroup> groups) async {
    final prefs = await SharedPreferences.getInstance();
    final str = jsonEncode(groups.map((g) => g.toJson()).toList());
    await prefs.setString(_groupsKey, str);
  }

  Future<List<LocalTask>> loadTasks() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString(_tasksKey);
    if (str == null) return [];
    final List list = jsonDecode(str);
    return list.map((t) => LocalTask.fromJson(t)).toList();
  }

  Future<void> saveTasks(List<LocalTask> tasks) async {
    final prefs = await SharedPreferences.getInstance();
    final str = jsonEncode(tasks.map((t) => t.toJson()).toList());
    await prefs.setString(_tasksKey, str);
  }

  Future<List<LocalRecord>> loadRecords() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString(_recordsKey);
    if (str == null) return [];
    final List list = jsonDecode(str);
    return list.map((r) => LocalRecord.fromJson(r)).toList();
  }

  Future<void> saveRecords(List<LocalRecord> records) async {
    final prefs = await SharedPreferences.getInstance();
    final str = jsonEncode(records.map((r) => r.toJson()).toList());
    await prefs.setString(_recordsKey, str);
  }
}
