import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/storage/local_storage_service.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/priority_badge.dart';
import 'standalone_provider.dart';

/// Bitta talabaning barcha vazifalari: matritsaning teskari ko'rinishi.
/// Vazifa ichida talabalarni belgilash o'rniga, talaba ichida vazifalarni
/// belgilash va uning umumiy o'zlashtirishini bir ekranda ko'rish.
class StudentTasksScreen extends StatelessWidget {
  final LocalStudent student;
  final String groupId;

  const StudentTasksScreen({
    super.key,
    required this.student,
    required this.groupId,
  });

  void _openScoreDialog(
    BuildContext context,
    LocalTask task,
    LocalRecord? existing,
  ) {
    final feedbackController = TextEditingController(text: existing?.feedback ?? '');
    double sliderVal = (existing?.score ?? task.maxScore).toDouble().clamp(0, task.maxScore.toDouble());

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (dialogCtx, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Text(task.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Talaba: ${student.name}', style: const TextStyle(fontSize: 13, color: Colors.grey)),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Baho (Ball):', style: TextStyle(fontWeight: FontWeight.w600)),
                  Text(
                    '${sliderVal.toInt()} / ${task.maxScore}',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.primary),
                  ),
                ],
              ),
              Slider(
                value: sliderVal,
                min: 0,
                max: task.maxScore.toDouble(),
                divisions: task.maxScore > 0 ? task.maxScore : 1,
                activeColor: AppColors.primary,
                onChanged: (val) => setDialogState(() => sliderVal = val),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: feedbackController,
                maxLines: 2,
                decoration: InputDecoration(
                  labelText: 'O\'qituvchi izohi (ixtiyoriy)',
                  hintText: 'Masalan: Yaxshi, lekin 2-savol to\'liq emas',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
            ElevatedButton(
              onPressed: () {
                context.read<StandaloneProvider>().toggleRecord(
                      taskId: task.id,
                      studentId: student.id,
                      isDone: true,
                      score: sliderVal.toInt(),
                      feedback: feedbackController.text.trim(),
                    );
                Navigator.of(ctx).pop();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('${task.title} uchun baho saqlandi'),
                    duration: const Duration(seconds: 1),
                    backgroundColor: AppColors.success,
                  ),
                );
              },
              child: const Text('Saqlash'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<StandaloneProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final now = DateTime.now();

    final group = prov.groups.where((g) => g.id == groupId).firstOrNull;
    final tasks = prov.tasks.where((t) => t.groupId == groupId).toList();

    final doneCount = tasks.where((t) {
      final rec = prov.getRecord(t.id, student.id);
      return rec != null && rec.isDone;
    }).length;

    // Muddati o'tgan, lekin hali bajarilmagan vazifalar — "qarzdorlik".
    final overdueCount = tasks.where((t) {
      final rec = prov.getRecord(t.id, student.id);
      if (rec != null && rec.isDone) return false;
      final dl = DateTime.tryParse(t.deadline);
      return dl != null && dl.isBefore(now);
    }).length;

    final earnedScore = tasks.fold<int>(0, (sum, t) {
      final rec = prov.getRecord(t.id, student.id);
      return sum + ((rec != null && rec.isDone) ? rec.score : 0);
    });
    final possibleScore = tasks.fold<int>(0, (sum, t) => sum + t.maxScore);
    final scorePercent = possibleScore > 0 ? (earnedScore / possibleScore * 100).round() : 0;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(student.name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800)),
            Text(
              group?.name ?? 'Guruh',
              style: const TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Talaba xulosasi
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            margin: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF4338CA), Color(0xFF6366F1)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 22,
                      backgroundColor: Colors.white.withValues(alpha: 0.2),
                      child: Text(
                        student.name.isNotEmpty ? student.name[0].toUpperCase() : 'T',
                        style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.white, fontSize: 18),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            student.name,
                            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Colors.white),
                          ),
                          Text(
                            student.phone != null && student.phone!.isNotEmpty
                                ? student.phone!
                                : 'Telefon kiritilmagan',
                            style: const TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    _summaryTile('Bajarilgan', '$doneCount / ${tasks.length}'),
                    _summaryTile('Umumiy ball', '$earnedScore / $possibleScore'),
                    _summaryTile('O\'zlashtirish', '$scorePercent%'),
                  ],
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: tasks.isNotEmpty ? doneCount / tasks.length : 0.0,
                    minHeight: 6,
                    backgroundColor: Colors.white.withValues(alpha: 0.2),
                    valueColor: const AlwaysStoppedAnimation<Color>(Colors.greenAccent),
                  ),
                ),
              ],
            ),
          ),

          // Bo'lim sarlavhasi + qarzdorlik ko'rsatkichi
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Text(
                  'Vazifalar (${tasks.length})',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
                  ),
                ),
                const Spacer(),
                if (overdueCount > 0)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.danger.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '$overdueCount ta qarzdorlik',
                      style: const TextStyle(
                        color: AppColors.danger,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 6),

          Expanded(
            child: tasks.isEmpty
                ? const Center(child: Text('Bu guruhda hali vazifa yo\'q.'))
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
                    itemCount: tasks.length,
                    itemBuilder: (ctx, idx) {
                      final task = tasks[idx];
                      final rec = prov.getRecord(task.id, student.id);
                      final isDone = rec != null && rec.isDone;

                      final deadlineDate = DateTime.tryParse(task.deadline);
                      final deadlineStr =
                          deadlineDate != null ? DateFormat('d MMM').format(deadlineDate) : task.deadline;
                      final isOverdue = !isDone && deadlineDate != null && deadlineDate.isBefore(now);

                      final borderColor = isDone
                          ? AppColors.success.withValues(alpha: 0.5)
                          : isOverdue
                              ? AppColors.danger.withValues(alpha: 0.5)
                              : (isDark ? AppColors.darkBorder : AppColors.lightBorder);

                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                          side: BorderSide(color: borderColor, width: (isDone || isOverdue) ? 1.5 : 1),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    isDone ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
                                    color: isDone
                                        ? AppColors.success
                                        : isOverdue
                                            ? AppColors.danger
                                            : Colors.grey,
                                    size: 22,
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      task.title,
                                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                                    ),
                                  ),
                                  PriorityBadge(priority: task.priority),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Row(
                                children: [
                                  Icon(
                                    Icons.event_rounded,
                                    size: 14,
                                    color: isOverdue ? AppColors.danger : Colors.grey,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    isOverdue ? '$deadlineStr — muddati o\'tgan' : deadlineStr,
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      color: isOverdue ? AppColors.danger : Colors.grey,
                                    ),
                                  ),
                                  const Spacer(),
                                  if (isDone)
                                    Text(
                                      'Baho: ${rec.score} / ${task.maxScore}',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w700,
                                        color: AppColors.primary,
                                      ),
                                    ),
                                ],
                              ),
                              if (rec?.feedback != null && rec!.feedback!.isNotEmpty) ...[
                                const SizedBox(height: 6),
                                Text(
                                  'Izoh: ${rec.feedback!}',
                                  style: const TextStyle(fontSize: 11.5, color: Colors.grey),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                              const SizedBox(height: 10),
                              Row(
                                children: [
                                  Expanded(
                                    child: OutlinedButton.icon(
                                      onPressed: () => _openScoreDialog(context, task, rec),
                                      icon: const Icon(Icons.edit_note_rounded, size: 18),
                                      label: const Text('Baho / Izoh', style: TextStyle(fontSize: 12.5)),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: ElevatedButton(
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: isDone
                                            ? AppColors.success
                                            : (isDark ? AppColors.darkSurfaceElevated : Colors.grey.shade200),
                                        foregroundColor:
                                            isDone ? Colors.white : (isDark ? Colors.white70 : Colors.black87),
                                        elevation: 0,
                                        padding: const EdgeInsets.symmetric(vertical: 10),
                                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                      ),
                                      onPressed: () {
                                        prov.toggleRecord(
                                          taskId: task.id,
                                          studentId: student.id,
                                          isDone: !isDone,
                                          score: !isDone ? task.maxScore : 0,
                                          feedback: rec?.feedback,
                                        );
                                      },
                                      child: Text(
                                        isDone ? 'Bajarildi' : 'Belgilash',
                                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12.5),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _summaryTile(String label, String value) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
          const SizedBox(height: 2),
          Text(
            value,
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 15),
          ),
        ],
      ),
    );
  }
}
