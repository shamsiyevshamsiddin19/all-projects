import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/custom_button.dart';
import '../../shared/widgets/custom_text_field.dart';
import '../../shared/widgets/empty_state_view.dart';
import '../../shared/widgets/priority_badge.dart';
import '../../shared/widgets/status_badge.dart';
import '../auth/auth_provider.dart';
import '../submissions/submission_review_modal.dart';
import 'assignment_provider.dart';

class AssignmentDetailScreen extends StatefulWidget {
  final String assignmentId;

  const AssignmentDetailScreen({super.key, required this.assignmentId});

  @override
  State<AssignmentDetailScreen> createState() => _AssignmentDetailScreenState();
}

class _AssignmentDetailScreenState extends State<AssignmentDetailScreen> {
  final _answerController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final prov = context.read<AssignmentProvider>();
      prov.fetchAssignmentDetail(widget.assignmentId);
      if (context.read<AuthProvider>().user?.isTeacher ?? false) {
        prov.fetchSubmissionsForAssignment(widget.assignmentId);
      }
    });
  }

  @override
  void dispose() {
    _answerController.dispose();
    super.dispose();
  }

  void _onSubmit() async {
    if (_answerController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Javob matnini kiriting"),
          backgroundColor: AppColors.warning,
        ),
      );
      return;
    }

    final assignProv = context.read<AssignmentProvider>();
    final ok = await assignProv.submitTask(
      assignmentId: widget.assignmentId,
      answerText: _answerController.text.trim(),
      attachments: [],
    );

    if (!mounted) return;
    if (ok) {
      _answerController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Topshiriq muvaffaqiyatli yuborildi! 🎉"),
          backgroundColor: AppColors.success,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final assignProv = context.watch<AssignmentProvider>();
    final a = assignProv.selectedAssignment;
    final isTeacher = auth.user?.isTeacher ?? false;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    if (assignProv.isLoading && a == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (a == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text("Vazifa topilmadi")),
      );
    }

    final deadlineDate = DateTime.tryParse(a.deadline);
    final formattedDeadline = deadlineDate != null
        ? DateFormat("d MMMM yyyy, HH:mm").format(deadlineDate)
        : a.deadline;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Vazifa Tafsilotlari"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Assignment Header Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
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
                            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                          ),
                        ),
                        PriorityBadge(priority: a.priority),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      a.description,
                      style: TextStyle(
                        fontSize: 14,
                        color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                        height: 1.4,
                      ),
                    ),
                    if (a.instructions != null && a.instructions!.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isDark ? AppColors.darkSurfaceElevated : AppColors.lightSurfaceElevated,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.info_outline_rounded, size: 16, color: AppColors.primary),
                                SizedBox(width: 6),
                                Text(
                                  "Yo'riqnoma:",
                                  style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: AppColors.primary),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            Text(
                              a.instructions!,
                              style: const TextStyle(fontSize: 13, height: 1.35),
                            ),
                          ],
                        ),
                      ),
                    ],
                    const Divider(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildMetaItem(Icons.event_rounded, "Muddat", formattedDeadline, isDanger: a.isOverdue),
                        _buildMetaItem(Icons.grade_rounded, "Ball", "${a.maxScore} ball", isAccent: true),
                        if (a.groupName != null)
                          _buildMetaItem(Icons.group_outlined, "Guruh", a.groupName!),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Teacher View: Submissions List
            if (isTeacher) ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    "Topshirilgan Ishlar (${assignProv.assignmentSubmissions.length})",
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh_rounded, size: 20),
                    onPressed: () => assignProv.fetchSubmissionsForAssignment(widget.assignmentId),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              if (assignProv.assignmentSubmissions.isEmpty)
                const EmptyStateView(
                  icon: Icons.hourglass_empty_rounded,
                  title: "Topshiriqlar yo'q",
                  message: "Talabalar hali ushbu vazifani topshirmagan.",
                )
              else
                ...assignProv.assignmentSubmissions.map((s) => Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        onTap: () async {
                          final refreshed = await showModalBottomSheet<bool>(
                            context: context,
                            isScrollControlled: true,
                            backgroundColor: Colors.transparent,
                            builder: (_) => SubmissionReviewModal(
                              submission: s,
                              maxScore: a.maxScore,
                            ),
                          );
                          if (refreshed == true) {
                            assignProv.fetchSubmissionsForAssignment(widget.assignmentId);
                          }
                        },
                        leading: CircleAvatar(
                          backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                          child: Text(
                            s.studentName?.isNotEmpty == true ? s.studentName![0].toUpperCase() : "T",
                            style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.primary),
                          ),
                        ),
                        title: Text(
                          s.studentName ?? "Talaba",
                          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5),
                        ),
                        subtitle: Text(
                          s.latestFeedback != null ? "Izoh: ${s.latestFeedback}" : (s.answerText ?? "Fayl biriktirilgan"),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 12),
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            if (s.latestScore != null)
                              Text(
                                "${s.latestScore}/${a.maxScore}",
                                style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.success,
                                  fontSize: 14,
                                ),
                              ),
                            StatusBadge(status: s.status, isLate: s.isLate),
                          ],
                        ),
                      ),
                    )),
            ] else ...[
              // Student View: Submission Area or Feedback
              if (a.isSubmittedByMe) ...[
                Card(
                  color: AppColors.success.withValues(alpha: 0.08),
                  child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.check_circle_rounded, color: AppColors.success, size: 24),
                            const SizedBox(width: 10),
                            const Text(
                              "Siz bu vazifani topshirdingiz!",
                              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15.5),
                            ),
                            const Spacer(),
                            StatusBadge(status: a.mySubmissionStatus ?? "SUBMITTED"),
                          ],
                        ),
                        if (a.myScore != null) ...[
                          const SizedBox(height: 14),
                          Text(
                            "Olingan Baho: ${a.myScore} / ${a.maxScore} ball",
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.primary),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  "Qayta topshirish:",
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 10),
              ],

              // Student Answer Box
              CustomTextField(
                label: "Sizning javobingiz",
                hint: "Javobingizni, kod yoki tushuntirishni yozing...",
                controller: _answerController,
                maxLines: 4,
              ),
              const SizedBox(height: 24),
              CustomButton(
                text: a.isSubmittedByMe ? "Qayta Topshirish" : "Vazifani Yuborish",
                onPressed: _onSubmit,
                isLoading: assignProv.isLoading,
                icon: Icons.send_rounded,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMetaItem(IconData icon, String label, String val, {bool isDanger = false, bool isAccent = false}) {
    Color col = isDanger ? AppColors.danger : (isAccent ? AppColors.primary : Colors.grey);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: col),
            const SizedBox(width: 4),
            Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          val,
          style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: col),
        ),
      ],
    );
  }
}
