import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/empty_state_view.dart';
import '../../shared/widgets/priority_badge.dart';
import '../../shared/widgets/status_badge.dart';
import '../auth/auth_provider.dart';
import 'assignment_detail_screen.dart';
import 'assignment_provider.dart';
import 'create_assignment_screen.dart';

class AssignmentsScreen extends StatefulWidget {
  const AssignmentsScreen({super.key});

  @override
  State<AssignmentsScreen> createState() => _AssignmentsScreenState();
}

class _AssignmentsScreenState extends State<AssignmentsScreen> {
  final _searchController = TextEditingController();
  String _selectedFilter = "all"; // all, active, completed, overdue

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AssignmentProvider>().fetchAssignments();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _applyFilter(String filter) {
    setState(() => _selectedFilter = filter);
    context.read<AssignmentProvider>().fetchAssignments(
          filterStatus: filter == "all" ? null : filter,
          search: _searchController.text.trim(),
        );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final assignProv = context.watch<AssignmentProvider>();
    final isTeacher = auth.user?.isTeacher ?? false;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Vazifalar"),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => _applyFilter(_selectedFilter),
          ),
        ],
      ),
      floatingActionButton: isTeacher
          ? FloatingActionButton.extended(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const CreateAssignmentScreen()),
                );
              },
              icon: const Icon(Icons.add_rounded),
              label: const Text("Vazifa Yaratish"),
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            )
          : null,
      body: Column(
        children: [
          // Search & Filter Header
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  onChanged: (v) {
                    context.read<AssignmentProvider>().fetchAssignments(
                          filterStatus: _selectedFilter == "all" ? null : _selectedFilter,
                          search: v.trim(),
                        );
                  },
                  decoration: InputDecoration(
                    hintText: "Vazifalarni qidirish...",
                    prefixIcon: const Icon(Icons.search_rounded, size: 20),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              _applyFilter(_selectedFilter);
                            },
                          )
                        : null,
                  ),
                ),
                const SizedBox(height: 10),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildFilterChip("all", "Barchasi"),
                      const SizedBox(width: 8),
                      _buildFilterChip("active", "Faol"),
                      const SizedBox(width: 8),
                      _buildFilterChip("completed", "Topshirilgan"),
                      const SizedBox(width: 8),
                      _buildFilterChip("overdue", "Muddati o'tgan"),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Assignments List
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async => _applyFilter(_selectedFilter),
              child: assignProv.isLoading && assignProv.assignments.isEmpty
                  ? const Center(child: CircularProgressIndicator())
                  : assignProv.assignments.isEmpty
                      ? EmptyStateView(
                          icon: Icons.task_outlined,
                          title: "Vazifalar topilmadi",
                          message: isTeacher
                              ? "Hozircha hech qanday vazifa yaratilmagan."
                              : "Sizda yangi vazifalar yo'q. Barcha vazifalar bajarilgan!",
                          buttonText: isTeacher ? "Yangi Vazifa" : null,
                          onButtonPressed: isTeacher
                              ? () => Navigator.of(context).push(
                                    MaterialPageRoute(builder: (_) => const CreateAssignmentScreen()),
                                  )
                              : null,
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          itemCount: assignProv.assignments.length,
                          itemBuilder: (ctx, idx) {
                            final a = assignProv.assignments[idx];
                            final deadlineDate = DateTime.tryParse(a.deadline);
                            final formattedDate = deadlineDate != null
                                ? DateFormat("d MMM, HH:mm").format(deadlineDate)
                                : a.deadline;

                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              child: InkWell(
                                borderRadius: BorderRadius.circular(16),
                                onTap: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => AssignmentDetailScreen(assignmentId: a.id),
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
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Expanded(
                                            child: Text(
                                              a.title,
                                              style: const TextStyle(
                                                fontSize: 15.5,
                                                fontWeight: FontWeight.w700,
                                              ),
                                            ),
                                          ),
                                          PriorityBadge(priority: a.priority),
                                        ],
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        a.description,
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                        style: TextStyle(
                                          fontSize: 13,
                                          color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                        ),
                                      ),
                                      const SizedBox(height: 12),
                                      Row(
                                        children: [
                                          Icon(
                                            Icons.access_time_rounded,
                                            size: 15,
                                            color: a.isOverdue ? AppColors.danger : Colors.grey,
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            formattedDate,
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: a.isOverdue ? AppColors.danger : Colors.grey,
                                              fontWeight: a.isOverdue ? FontWeight.w700 : FontWeight.w500,
                                            ),
                                          ),
                                          if (a.groupName != null) ...[
                                            const SizedBox(width: 10),
                                            Container(width: 3, height: 3, decoration: const BoxDecoration(color: Colors.grey, shape: BoxShape.circle)),
                                            const SizedBox(width: 10),
                                            Text(
                                              a.groupName!,
                                              style: const TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.w600),
                                            ),
                                          ],
                                          const Spacer(),
                                          if (isTeacher)
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                              decoration: BoxDecoration(
                                                color: AppColors.info.withValues(alpha: 0.12),
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Text(
                                                "${a.totalSubmitted} topshiriq",
                                                style: const TextStyle(fontSize: 11, color: AppColors.info, fontWeight: FontWeight.w600),
                                              ),
                                            )
                                          else if (a.isSubmittedByMe)
                                            StatusBadge(status: a.mySubmissionStatus ?? "SUBMITTED")
                                          else if (a.isOverdue)
                                            const StatusBadge(status: "LATE", isLate: true),
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
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String key, String label) {
    final isSelected = _selectedFilter == key;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => _applyFilter(key),
      labelStyle: TextStyle(
        fontSize: 12.5,
        fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
        color: isSelected ? Colors.white : null,
      ),
      selectedColor: AppColors.primary,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      showCheckmark: false,
    );
  }
}
