import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/empty_state_view.dart';
import '../auth/auth_provider.dart';
import 'group_provider.dart';

class GroupDetailScreen extends StatefulWidget {
  final String groupId;

  const GroupDetailScreen({super.key, required this.groupId});

  @override
  State<GroupDetailScreen> createState() => _GroupDetailScreenState();
}

class _GroupDetailScreenState extends State<GroupDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GroupProvider>().fetchGroupDetail(widget.groupId);
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final groupProv = context.watch<GroupProvider>();
    final group = groupProv.selectedGroup;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isTeacher = auth.user?.isTeacher ?? false;

    if (groupProv.isLoading || group == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(group.name),
        actions: [
          if (isTeacher)
            IconButton(
              icon: const Icon(Icons.delete_outline_rounded, color: AppColors.danger),
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    title: const Text("Guruhni o'chirish"),
                    content: const Text("Haqiqatan ham ushbu guruhni o'chirmoqchimisiz?"),
                    actions: [
                      TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text("Bekor qilish")),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
                        onPressed: () async {
                          Navigator.of(ctx).pop();
                          final ok = await groupProv.deleteGroup(group.id);
                          if (mounted && ok) {
                            Navigator.of(context).pop();
                          }
                        },
                        child: const Text("O'chirish"),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Group Info Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          group.name,
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                "Kod: ${group.inviteCode}",
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.primary,
                                ),
                              ),
                              const SizedBox(width: 6),
                              GestureDetector(
                                onTap: () {
                                  Clipboard.setData(ClipboardData(text: group.inviteCode));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text("Guruh kodi nusxalandi!"), duration: Duration(seconds: 1)),
                                  );
                                },
                                child: const Icon(Icons.copy_rounded, size: 16, color: AppColors.primary),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    if (group.description != null && group.description!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        group.description!,
                        style: TextStyle(
                          fontSize: 13.5,
                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        ),
                      ),
                    ],
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildStatCol("${group.members.length}", "Talabalar"),
                        Container(width: 1, height: 28, color: Colors.grey.withValues(alpha: 0.2)),
                        _buildStatCol("${group.totalAssignments}", "Vazifalar"),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Students Roster Section
            Text(
              "Guruh Talabalari (${group.members.length})",
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
              ),
            ),
            const SizedBox(height: 12),
            if (group.members.isEmpty)
              const EmptyStateView(
                icon: Icons.person_add_disabled_outlined,
                title: "Talabalar mavjud emas",
                message: "Guruhga qo'shilish uchun talabalarga taklif kodini ulashing.",
              )
            else
              ...group.members.map((m) => Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                        child: Text(
                          m.fullName.isNotEmpty ? m.fullName[0].toUpperCase() : "S",
                          style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.primary),
                        ),
                      ),
                      title: Text(
                        m.fullName,
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14.5),
                      ),
                      subtitle: Text(
                        m.email,
                        style: const TextStyle(fontSize: 12.5, color: Colors.grey),
                      ),
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppColors.success.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Text(
                          "Faol",
                          style: TextStyle(color: AppColors.success, fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ),
                  )),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCol(String val, String label) {
    return Column(
      children: [
        Text(
          val,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppColors.primary),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: const TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ],
    );
  }
}
