import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/empty_state_view.dart';
import '../auth/auth_provider.dart';
import 'group_detail_screen.dart';
import 'group_provider.dart';

class GroupsScreen extends StatefulWidget {
  const GroupsScreen({super.key});

  @override
  State<GroupsScreen> createState() => _GroupsScreenState();
}

class _GroupsScreenState extends State<GroupsScreen> {
  final _nameController = TextEditingController();
  final _descController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GroupProvider>().fetchGroups();
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _showCreateGroupModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
        child: Container(
          decoration: BoxDecoration(
            color: Theme.of(context).cardTheme.color,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
          ),
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(color: Colors.grey.shade600, borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 18),
              const Text(
                "Yangi Guruh Yaratish",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 6),
              const Text(
                "Guruh yaratilgach unikal 6 xonali taklif kodi avtomatik beriladi.",
                style: TextStyle(fontSize: 12.5, color: Colors.grey),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _nameController,
                decoration: InputDecoration(
                  labelText: "Guruh nomi",
                  hintText: "Masalan: Frontend 2026",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: _descController,
                maxLines: 2,
                decoration: InputDecoration(
                  labelText: "Tavsif (ixtiyoriy)",
                  hintText: "Dars vaqtlari, yo'nalish haqida qisqacha",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: () async {
                    if (_nameController.text.trim().isEmpty) return;
                    Navigator.of(ctx).pop();
                    final success = await context.read<GroupProvider>().createGroup(
                          _nameController.text.trim(),
                          _descController.text.trim(),
                        );
                    if (mounted && success) {
                      _nameController.clear();
                      _descController.clear();
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text("Guruh muvaffaqiyatli yaratildi! 🎉"),
                          backgroundColor: AppColors.success,
                        ),
                      );
                    }
                  },
                  child: const Text("Guruhni Saqlash"),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final groupProv = context.watch<GroupProvider>();
    final isTeacher = auth.user?.isTeacher ?? false;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Guruhlar"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => groupProv.fetchGroups(),
          ),
        ],
      ),
      floatingActionButton: isTeacher
          ? FloatingActionButton.extended(
              onPressed: _showCreateGroupModal,
              icon: const Icon(Icons.add_rounded),
              label: const Text("Yangi Guruh"),
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            )
          : null,
      body: RefreshIndicator(
        onRefresh: () => groupProv.fetchGroups(),
        child: groupProv.isLoading && groupProv.groups.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : groupProv.groups.isEmpty
                ? EmptyStateView(
                    icon: Icons.groups_outlined,
                    title: "Guruhlar mavjud emas",
                    message: isTeacher
                        ? "O'quvchilaringiz uchun yangi guruh yarating va ularga taklif kodini bering."
                        : "Siz hali hech qaysi guruhga qo'shilmagansiz. Taklif kodini kiriting.",
                    buttonText: isTeacher ? "Guruh Yaratish" : null,
                    onButtonPressed: isTeacher ? _showCreateGroupModal : null,
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    itemCount: groupProv.groups.length,
                    itemBuilder: (ctx, idx) {
                      final group = groupProv.groups[idx];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(16),
                          onTap: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => GroupDetailScreen(groupId: group.id),
                              ),
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
                                        group.name,
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: AppColors.primary.withValues(alpha: 0.12),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Text(
                                            group.inviteCode,
                                            style: const TextStyle(
                                              fontSize: 12.5,
                                              fontWeight: FontWeight.w700,
                                              color: AppColors.primary,
                                              letterSpacing: 1.5,
                                            ),
                                          ),
                                          const SizedBox(width: 4),
                                          GestureDetector(
                                            onTap: () {
                                              Clipboard.setData(ClipboardData(text: group.inviteCode));
                                              ScaffoldMessenger.of(context).showSnackBar(
                                                const SnackBar(
                                                  content: Text("Taklif kodi nusxalandi!"),
                                                  duration: Duration(seconds: 1),
                                                ),
                                              );
                                            },
                                            child: const Icon(Icons.copy_rounded, size: 14, color: AppColors.primary),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                                if (group.description != null && group.description!.isNotEmpty) ...[
                                  const SizedBox(height: 6),
                                  Text(
                                    group.description!,
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                    ),
                                    maxLines: 2,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                                const SizedBox(height: 14),
                                Row(
                                  children: [
                                    _buildInfoChip(
                                      icon: Icons.people_alt_outlined,
                                      label: "${group.totalStudents} talaba",
                                    ),
                                    const SizedBox(width: 12),
                                    _buildInfoChip(
                                      icon: Icons.assignment_outlined,
                                      label: "${group.totalAssignments} vazifa",
                                    ),
                                    const Spacer(),
                                    const Icon(Icons.chevron_right_rounded, color: Colors.grey),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  ),
      ),
    );
  }

  Widget _buildInfoChip({required IconData icon, required String label}) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: Colors.grey),
        const SizedBox(width: 4),
        Text(
          label,
          style: const TextStyle(fontSize: 12.5, color: Colors.grey, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }
}
