import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/storage/local_storage_service.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/priority_badge.dart';
import '../../shared/widgets/stat_card.dart';
import '../auth/auth_provider.dart';
import 'classroom_task_matrix_screen.dart';
import 'standalone_provider.dart';
import 'student_tasks_screen.dart';

class TeacherHomeScreen extends StatefulWidget {
  const TeacherHomeScreen({super.key});

  @override
  State<TeacherHomeScreen> createState() => _TeacherHomeScreenState();
}

class _TeacherHomeScreenState extends State<TeacherHomeScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _studentSearchCtrl = TextEditingController();
  String _studentQuery = '';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    // Tab almashganda FAB yozuvi ("Vazifa" / "Talaba") yangilanishi uchun.
    _tabController.addListener(() {
      if (mounted) setState(() {});
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StandaloneProvider>().init();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _studentSearchCtrl.dispose();
    super.dispose();
  }

  void _showGroupPickerSheet() {
    final searchCtrl = TextEditingController();
    String query = '';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setSheetState) {
          final prov = context.watch<StandaloneProvider>();
          final filtered = prov.groups.where((g) {
            if (query.isEmpty) return true;
            return g.name.toLowerCase().contains(query.toLowerCase());
          }).toList()
            ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

          return Padding(
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
            child: Container(
              constraints: BoxConstraints(maxHeight: MediaQuery.of(ctx).size.height * 0.75),
              decoration: BoxDecoration(
                color: Theme.of(context).cardTheme.color,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const SizedBox(height: 12),
                  Container(width: 36, height: 4, decoration: BoxDecoration(color: Colors.grey.shade600, borderRadius: BorderRadius.circular(2))),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
                    child: Row(
                      children: [
                        Text(
                          'Guruhlar (${prov.groups.length})',
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                        ),
                        const Spacer(),
                        TextButton.icon(
                          onPressed: () {
                            Navigator.of(ctx).pop();
                            _showAddGroupDialog();
                          },
                          icon: const Icon(Icons.add_rounded, size: 18),
                          label: const Text('Yangi guruh'),
                        ),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: TextField(
                      controller: searchCtrl,
                      autofocus: prov.groups.length > 6,
                      onChanged: (v) => setSheetState(() => query = v),
                      decoration: InputDecoration(
                        hintText: 'Guruhni qidirish...',
                        prefixIcon: const Icon(Icons.search_rounded, size: 20),
                        isDense: true,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Flexible(
                    child: filtered.isEmpty
                        ? const Padding(
                            padding: EdgeInsets.all(24),
                            child: Text('Hech qanday guruh topilmadi', style: TextStyle(color: Colors.grey)),
                          )
                        : ListView.builder(
                            shrinkWrap: true,
                            padding: const EdgeInsets.fromLTRB(12, 0, 12, 20),
                            itemCount: filtered.length,
                            itemBuilder: (ctx2, idx) {
                              final g = filtered[idx];
                              final isSelected = g.id == prov.selectedGroupId;
                              return ListTile(
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                                selected: isSelected,
                                selectedTileColor: AppColors.primary.withValues(alpha: 0.1),
                                leading: CircleAvatar(
                                  backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                                  child: Text(
                                    g.name.isNotEmpty ? g.name[0].toUpperCase() : 'G',
                                    style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.primary),
                                  ),
                                ),
                                title: Text(
                                  g.name,
                                  style: TextStyle(fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600, fontSize: 14.5),
                                ),
                                subtitle: Text('${g.students.length} nafar talaba', style: const TextStyle(fontSize: 12)),
                                trailing: isSelected ? const Icon(Icons.check_circle_rounded, color: AppColors.primary) : null,
                                onTap: () {
                                  prov.selectGroup(g.id);
                                  Navigator.of(ctx).pop();
                                },
                              );
                            },
                          ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  void _showAddGroupDialog() {
    final nameCtrl = TextEditingController();
    final descCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Yangi Guruh Qo\'shish', style: TextStyle(fontWeight: FontWeight.w800)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameCtrl,
              decoration: InputDecoration(
                labelText: 'Guruh nomi',
                hintText: 'Masalan: Python 1-guruh',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: descCtrl,
              decoration: InputDecoration(
                labelText: 'Dars vaqti / Tavsif',
                hintText: 'Dush / Chor / Juma 18:00',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
          ElevatedButton(
            onPressed: () {
              if (nameCtrl.text.trim().isEmpty) return;
              context.read<StandaloneProvider>().addGroup(nameCtrl.text.trim(), descCtrl.text.trim());
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Guruh yaratildi! 🎉'), backgroundColor: AppColors.success),
              );
            },
            child: const Text('Saqlash'),
          ),
        ],
      ),
    );
  }

  void _showAddStudentDialog(String groupId, {LocalStudent? existing}) {
    final isEdit = existing != null;
    final nameCtrl = TextEditingController(text: existing?.name ?? '');
    final phoneCtrl = TextEditingController(text: existing?.phone ?? '');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          isEdit ? 'Talaba Ma\'lumotini Tahrirlash' : 'Yangi Talaba Qo\'shish',
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameCtrl,
              decoration: InputDecoration(
                labelText: 'Talaba Ismi Familiyasi',
                hintText: 'Aziz Rahimov',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: phoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(
                labelText: 'Telefon raqami (ixtiyoriy)',
                hintText: '+998 90 123 45 67',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
          ElevatedButton(
            onPressed: () {
              if (nameCtrl.text.trim().isEmpty) return;
              if (isEdit) {
                context
                    .read<StandaloneProvider>()
                    .updateStudent(groupId, existing.id, nameCtrl.text.trim(), phoneCtrl.text.trim());
              } else {
                context.read<StandaloneProvider>().addStudent(groupId, nameCtrl.text.trim(), phoneCtrl.text.trim());
              }
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(isEdit ? 'Talaba ma\'lumoti yangilandi' : 'Talaba guruhga qo\'shildi! ✅'),
                  backgroundColor: AppColors.success,
                ),
              );
            },
            child: Text(isEdit ? 'Saqlash' : 'Qo\'shish'),
          ),
        ],
      ),
    );
  }

  void _confirmDeleteStudent(LocalGroup group, LocalStudent student) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Talabani o\'chirish'),
        content: Text(
          '${student.name} guruhdan va barcha baholaridan butunlay o\'chiriladi. Bu amalni ortga qaytarib bo\'lmaydi.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () {
              context.read<StandaloneProvider>().deleteStudent(group.id, student.id);
              Navigator.of(ctx).pop();
            },
            child: const Text('O\'chirish'),
          ),
        ],
      ),
    );
  }

  void _showAddTaskDialog(String groupId, {LocalTask? existing}) {
    final isEdit = existing != null;
    final titleCtrl = TextEditingController(text: existing?.title ?? '');
    final descCtrl = TextEditingController(text: existing?.description ?? '');
    final scoreCtrl = TextEditingController(text: '${existing?.maxScore ?? 100}');
    DateTime selectedDeadline =
        (existing != null ? DateTime.tryParse(existing.deadline) : null) ?? DateTime.now().add(const Duration(days: 3));
    String selectedPriority = existing?.priority ?? 'MEDIUM';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setModalState) => Padding(
          padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
          child: Container(
            decoration: BoxDecoration(
              color: Theme.of(context).cardTheme.color,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            ),
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(width: 36, height: 4, decoration: BoxDecoration(color: Colors.grey.shade600, borderRadius: BorderRadius.circular(2))),
                ),
                const SizedBox(height: 16),
                Text(
                  isEdit ? 'Vazifani Tahrirlash' : 'Yangi Vazifa / Uy ishi Yaratish',
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: titleCtrl,
                  decoration: InputDecoration(
                    labelText: 'Vazifa sarlavhasi',
                    hintText: 'Masalan: 3-Dars: Funksiyalar va Rekursiya',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: descCtrl,
                  maxLines: 2,
                  decoration: InputDecoration(
                    labelText: 'Vazifa sharti va topshiriqlar',
                    hintText: 'Kitobdagi 15-mashqni yechish',
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 12),
                // Muddat tanlagich — avval bu doim "bugun + 3 kun" bo'lib
                // qattiq belgilangan edi, o'qituvchi o'zgartira olmas edi.
                InkWell(
                  borderRadius: BorderRadius.circular(12),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: selectedDeadline,
                      firstDate: DateTime.now().subtract(const Duration(days: 365)),
                      lastDate: DateTime.now().add(const Duration(days: 365 * 2)),
                    );
                    if (picked != null) {
                      setModalState(() => selectedDeadline = picked);
                    }
                  },
                  child: InputDecorator(
                    decoration: InputDecoration(
                      labelText: 'Topshirish muddati',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      suffixIcon: const Icon(Icons.calendar_month_rounded, size: 20),
                    ),
                    child: Text(DateFormat('d MMMM yyyy').format(selectedDeadline)),
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        initialValue: selectedPriority,
                        decoration: InputDecoration(
                          labelText: 'Ustuvorlik',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'LOW', child: Text('Past')),
                          DropdownMenuItem(value: 'MEDIUM', child: Text('O\'rtacha')),
                          DropdownMenuItem(value: 'HIGH', child: Text('Yuqori')),
                          DropdownMenuItem(value: 'URGENT', child: Text('Shoshilinch')),
                        ],
                        onChanged: (v) {
                          if (v != null) setModalState(() => selectedPriority = v);
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: scoreCtrl,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText: 'Maks. Ball',
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: () {
                      if (titleCtrl.text.trim().isEmpty) return;
                      final score = int.tryParse(scoreCtrl.text) ?? 100;
                      final prov = context.read<StandaloneProvider>();
                      if (isEdit) {
                        prov.updateTask(
                          taskId: existing.id,
                          title: titleCtrl.text.trim(),
                          description: descCtrl.text.trim(),
                          maxScore: score,
                          deadline: selectedDeadline,
                          priority: selectedPriority,
                        );
                      } else {
                        prov.addTask(
                          groupId: groupId,
                          title: titleCtrl.text.trim(),
                          description: descCtrl.text.trim(),
                          maxScore: score,
                          deadline: selectedDeadline,
                          priority: selectedPriority,
                        );
                      }
                      Navigator.of(ctx).pop();
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(isEdit ? 'Vazifa yangilandi' : 'Vazifa ro\'yxatga qo\'shildi! 🚀'),
                          backgroundColor: AppColors.success,
                        ),
                      );
                    },
                    child: Text(isEdit ? 'Saqlash' : 'Vazifani E\'lon Qilish'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _confirmDeleteTask(LocalTask task) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Vazifani o\'chirish'),
        content: Text('"${task.title}" o\'chiriladi, shu vazifa bo\'yicha barcha baholar ham yo\'qoladi.'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () {
              context.read<StandaloneProvider>().deleteTask(task.id);
              Navigator.of(ctx).pop();
            },
            child: const Text('O\'chirish'),
          ),
        ],
      ),
    );
  }

  void _exportPdf(String groupId) async {
    final path = await context.read<StandaloneProvider>().exportPdf(groupId);
    if (mounted && path != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('PDF Hisobot ochildi: $path'), backgroundColor: AppColors.success),
      );
    }
  }

  void _exportExcel(String groupId) async {
    final path = await context.read<StandaloneProvider>().exportExcel(groupId);
    if (mounted && path != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Excel Hisobot ochildi: $path'), backgroundColor: AppColors.success),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<StandaloneProvider>();
    final auth = context.watch<AuthProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final currentGroup = prov.currentGroup;
    final groupTasks = prov.currentGroupTasks;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Нилуфар Бурхонова', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
            Text(
              currentGroup != null ? currentGroup.name : 'Guruh tanlang',
              style: const TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.w600),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded),
            tooltip: 'Mavzuni o\'zgartirish',
            onPressed: () => auth.toggleTheme(),
          ),
          if (currentGroup != null)
            PopupMenuButton<String>(
              icon: const Icon(Icons.more_vert_rounded),
              onSelected: (val) {
                if (val == 'pdf') _exportPdf(currentGroup.id);
                if (val == 'excel') _exportExcel(currentGroup.id);
                if (val == 'delete') {
                  showDialog(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      title: const Text('Guruhni o\'chirish'),
                      content: Text('${currentGroup.name} guruhini o\'chirmoqchimisiz?'),
                      actions: [
                        TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
                          onPressed: () {
                            prov.deleteGroup(currentGroup.id);
                            Navigator.of(ctx).pop();
                          },
                          child: const Text('O\'chirish'),
                        ),
                      ],
                    ),
                  );
                }
              },
              itemBuilder: (ctx) => [
                const PopupMenuItem(
                  value: 'pdf',
                  child: Row(children: [Icon(Icons.picture_as_pdf_rounded, color: AppColors.danger, size: 18), SizedBox(width: 10), Text('PDF Hisobot Yuklash')]),
                ),
                const PopupMenuItem(
                  value: 'excel',
                  child: Row(children: [Icon(Icons.table_chart_rounded, color: AppColors.success, size: 18), SizedBox(width: 10), Text('Excel (XLSX) Yuklash')]),
                ),
                const PopupMenuDivider(),
                const PopupMenuItem(
                  value: 'delete',
                  child: Row(children: [Icon(Icons.delete_outline_rounded, color: AppColors.danger, size: 18), SizedBox(width: 10), Text('Guruhni o\'chirish', style: TextStyle(color: AppColors.danger))]),
                ),
              ],
            ),
        ],
      ),
      body: prov.isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Guruh tanlagich. Avval bu gorizontal skrol qilinadigan
                // chiplar qatori edi — 15-20 ta guruh bo'lganda kerakli
                // guruhni topish uchun uzoq skrol qilish kerak bo'lar edi.
                // Endi qidiruvli ro'yxat (bottom sheet) sifatida ochiladi.
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
                  child: Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: prov.groups.isEmpty ? _showAddGroupDialog : _showGroupPickerSheet,
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                            decoration: BoxDecoration(
                              color: isDark ? AppColors.darkSurfaceElevated : AppColors.lightSurfaceElevated,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                            ),
                            child: Row(
                              children: [
                                const Icon(Icons.groups_rounded, size: 18, color: AppColors.primary),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: Text(
                                    currentGroup != null
                                        ? currentGroup.name
                                        : 'Avval guruh yarating',
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                                  ),
                                ),
                                if (prov.groups.length > 1)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: AppColors.primary.withValues(alpha: 0.12),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      '${prov.groups.length} ta',
                                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.primary),
                                    ),
                                  ),
                                const SizedBox(width: 6),
                                Icon(Icons.unfold_more_rounded, size: 18, color: isDark ? AppColors.darkTextMuted : AppColors.lightTextMuted),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton.filledTonal(
                        onPressed: _showAddGroupDialog,
                        icon: const Icon(Icons.add_rounded),
                        tooltip: 'Yangi guruh',
                      ),
                    ],
                  ),
                ),

                // Group Metrics Header Cards
                if (currentGroup != null)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 6, 16, 8),
                    child: Row(
                      children: [
                        Expanded(
                          child: StatCard(
                            title: 'Talabalar',
                            value: '${currentGroup.students.length}',
                            icon: Icons.people_alt_outlined,
                            iconColor: AppColors.info,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: StatCard(
                            title: 'Vazifalar',
                            value: '${groupTasks.length}',
                            icon: Icons.assignment_outlined,
                            iconColor: AppColors.primary,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: StatCard(
                            title: 'O\'zlashtirish',
                            value: '${prov.completionRateForGroup(currentGroup.id).toInt()}%',
                            icon: Icons.done_all_rounded,
                            iconColor: AppColors.success,
                          ),
                        ),
                      ],
                    ),
                  ),

                // Tab Bar: 1. Vazifalar (Tasks) | 2. Talabalar (Students)
                TabBar(
                  controller: _tabController,
                  indicatorColor: AppColors.primary,
                  labelColor: AppColors.primary,
                  unselectedLabelColor: Colors.grey,
                  tabs: [
                    Tab(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.task_alt_rounded, size: 18),
                          const SizedBox(width: 6),
                          Text('Vazifalar (${groupTasks.length})'),
                        ],
                      ),
                    ),
                    Tab(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.groups_rounded, size: 18),
                          const SizedBox(width: 6),
                          Text('Talabalar (${currentGroup?.students.length ?? 0})'),
                        ],
                      ),
                    ),
                  ],
                ),

                // Tab Views
                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      // TAB 1: Tasks List
                      _buildTasksTab(groupTasks, currentGroup),

                      // TAB 2: Students List
                      _buildStudentsTab(currentGroup),
                    ],
                  ),
                ),
              ],
            ),
      floatingActionButton: currentGroup == null
          ? null
          : FloatingActionButton.extended(
              onPressed: () {
                if (_tabController.index == 0) {
                  _showAddTaskDialog(currentGroup.id);
                } else {
                  _showAddStudentDialog(currentGroup.id);
                }
              },
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.add_rounded),
              label: Text(_tabController.index == 0 ? 'Vazifa Qo\'shish' : 'Talaba Qo\'shish'),
            ),
    );
  }

  Widget _buildTasksTab(List<LocalTask> tasks, LocalGroup? currentGroup) {
    if (currentGroup == null || tasks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.assignment_outlined, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            const Text('Hozircha vazifalar yo\'q', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 6),
            const Text('Dars vazifasini qo\'shish uchun pastdagi tugmani bosing.', style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 16),
            if (currentGroup != null)
              ElevatedButton.icon(
                onPressed: () => _showAddTaskDialog(currentGroup.id),
                icon: const Icon(Icons.add),
                label: const Text('Vazifa Yaratish'),
              ),
          ],
        ),
      );
    }

    final prov = context.read<StandaloneProvider>();

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: tasks.length,
      itemBuilder: (ctx, idx) {
        final t = tasks[idx];
        final deadlineDate = DateTime.tryParse(t.deadline);
        final deadlineStr = deadlineDate != null ? DateFormat('d MMM').format(deadlineDate) : t.deadline;

        final doneCount = currentGroup.students.where((s) {
          final rec = prov.getRecord(t.id, s.id);
          return rec != null && rec.isDone;
        }).length;

        final double progress = currentGroup.students.isNotEmpty ? (doneCount / currentGroup.students.length) : 0.0;

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => ClassroomTaskMatrixScreen(task: t)),
              );
            },
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          t.title,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15.5),
                        ),
                      ),
                      const SizedBox(width: 8),
                      PriorityBadge(priority: t.priority),
                      PopupMenuButton<String>(
                        padding: EdgeInsets.zero,
                        icon: const Icon(Icons.more_vert_rounded, size: 20, color: Colors.grey),
                        onSelected: (val) {
                          if (val == 'edit') _showAddTaskDialog(currentGroup.id, existing: t);
                          if (val == 'delete') _confirmDeleteTask(t);
                        },
                        itemBuilder: (ctx) => const [
                          PopupMenuItem(
                            value: 'edit',
                            child: Row(children: [
                              Icon(Icons.edit_rounded, size: 18, color: AppColors.primary),
                              SizedBox(width: 10),
                              Text('Tahrirlash'),
                            ]),
                          ),
                          PopupMenuItem(
                            value: 'delete',
                            child: Row(children: [
                              Icon(Icons.delete_outline_rounded, size: 18, color: AppColors.danger),
                              SizedBox(width: 10),
                              Text('O\'chirish', style: TextStyle(color: AppColors.danger)),
                            ]),
                          ),
                        ],
                      ),
                    ],
                  ),
                  if (t.description.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(
                      t.description,
                      style: const TextStyle(color: Colors.grey, fontSize: 13),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.event_rounded, size: 14, color: Colors.grey),
                          const SizedBox(width: 4),
                          Text(deadlineStr, style: const TextStyle(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.w600)),
                        ],
                      ),
                      Text(
                        '$doneCount / ${currentGroup.students.length} bajarildi',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.primary),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: progress,
                      minHeight: 5,
                      backgroundColor: Colors.grey.withValues(alpha: 0.15),
                      valueColor: AlwaysStoppedAnimation<Color>(progress == 1.0 ? AppColors.success : AppColors.primary),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildStudentsTab(LocalGroup? currentGroup) {
    if (currentGroup == null || currentGroup.students.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.people_outline_rounded, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            const Text('Guruhda talabalar yo\'q', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 6),
            const Text('Darsga kelgan talabalarni qo\'shing.', style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 16),
            if (currentGroup != null)
              ElevatedButton.icon(
                onPressed: () => _showAddStudentDialog(currentGroup.id),
                icon: const Icon(Icons.person_add_rounded),
                label: const Text('Talaba Qo\'shish'),
              ),
          ],
        ),
      );
    }

    final prov = context.read<StandaloneProvider>();
    final groupTasks = prov.currentGroupTasks;

    // Alifbo tartibi + qidiruv — 20-30 kishilik guruhda kerakli talabani
    // scroll qilmasdan topish uchun.
    final filtered = currentGroup.students.where((s) {
      if (_studentQuery.isEmpty) return true;
      return s.name.toLowerCase().contains(_studentQuery.toLowerCase());
    }).toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: TextField(
            controller: _studentSearchCtrl,
            onChanged: (v) => setState(() => _studentQuery = v),
            decoration: InputDecoration(
              hintText: 'Talabani qidirish...',
              prefixIcon: const Icon(Icons.search_rounded, size: 20),
              suffixIcon: _studentQuery.isEmpty
                  ? null
                  : IconButton(
                      icon: const Icon(Icons.close_rounded, size: 18),
                      onPressed: () => setState(() {
                        _studentSearchCtrl.clear();
                        _studentQuery = '';
                      }),
                    ),
              isDense: true,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
        Expanded(
          child: filtered.isEmpty
              ? const Center(child: Text('Hech kim topilmadi', style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  itemCount: filtered.length,
                  itemBuilder: (ctx, idx) {
                    final st = filtered[idx];

                    final doneTasksCount = groupTasks.where((t) {
                      final rec = prov.getRecord(t.id, st.id);
                      return rec != null && rec.isDone;
                    }).length;

                    return Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        contentPadding: const EdgeInsets.only(left: 12, right: 4),
                        horizontalTitleGap: 10,
                        onTap: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => StudentTasksScreen(student: st, groupId: currentGroup.id),
                            ),
                          );
                        },
                        leading: CircleAvatar(
                          backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                          child: Text(
                            st.name.isNotEmpty ? st.name[0].toUpperCase() : 'T',
                            style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.primary),
                          ),
                        ),
                        title: Text(
                          st.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5),
                        ),
                        subtitle: Text(
                          st.phone != null && st.phone!.isNotEmpty ? st.phone! : 'Telefon kiritilmagan',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.success.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                '$doneTasksCount / ${groupTasks.length}',
                                style: const TextStyle(
                                  color: AppColors.success,
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            PopupMenuButton<String>(
                              padding: EdgeInsets.zero,
                              icon: const Icon(Icons.more_vert_rounded, color: Colors.grey, size: 20),
                              onSelected: (val) {
                                if (val == 'edit') {
                                  _showAddStudentDialog(currentGroup.id, existing: st);
                                }
                                if (val == 'delete') {
                                  _confirmDeleteStudent(currentGroup, st);
                                }
                              },
                              itemBuilder: (ctx) => const [
                                PopupMenuItem(
                                  value: 'edit',
                                  child: Row(children: [
                                    Icon(Icons.edit_rounded, size: 18, color: AppColors.primary),
                                    SizedBox(width: 10),
                                    Text('Tahrirlash'),
                                  ]),
                                ),
                                PopupMenuItem(
                                  value: 'delete',
                                  child: Row(children: [
                                    Icon(Icons.delete_outline_rounded, size: 18, color: AppColors.danger),
                                    SizedBox(width: 10),
                                    Text('O\'chirish', style: TextStyle(color: AppColors.danger)),
                                  ]),
                                ),
                              ],
                            ),
                            const Icon(Icons.chevron_right_rounded, color: Colors.grey, size: 20),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}
