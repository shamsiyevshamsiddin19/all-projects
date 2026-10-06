import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/storage/local_storage_service.dart';
import '../../core/theme/app_colors.dart';
import 'standalone_provider.dart';

class ClassroomTaskMatrixScreen extends StatefulWidget {
  final LocalTask task;

  const ClassroomTaskMatrixScreen({super.key, required this.task});

  @override
  State<ClassroomTaskMatrixScreen> createState() => _ClassroomTaskMatrixScreenState();
}

class _ClassroomTaskMatrixScreenState extends State<ClassroomTaskMatrixScreen> {
  void _openScoreDialog(BuildContext context, LocalStudent student, LocalRecord? existing) {
    final scoreController = TextEditingController(text: existing != null ? '${existing.score}' : '${widget.task.maxScore}');
    final feedbackController = TextEditingController(text: existing?.feedback ?? '');
    double sliderVal = double.tryParse(scoreController.text) ?? widget.task.maxScore.toDouble();

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
          title: Text(
            student.name,
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Vazifa: ${widget.task.title}',
                style: const TextStyle(fontSize: 13, color: Colors.grey),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('Baho (Ball):', style: TextStyle(fontWeight: FontWeight.w600)),
                  Text(
                    '${sliderVal.toInt()} / ${widget.task.maxScore}',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.primary),
                  ),
                ],
              ),
              Slider(
                value: sliderVal.clamp(0, widget.task.maxScore.toDouble()),
                min: 0,
                max: widget.task.maxScore.toDouble(),
                divisions: widget.task.maxScore,
                activeColor: AppColors.primary,
                onChanged: (val) {
                  setDialogState(() {
                    sliderVal = val;
                    scoreController.text = '${val.toInt()}';
                  });
                },
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
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('Bekor qilish'),
            ),
            ElevatedButton(
              onPressed: () {
                final score = int.tryParse(scoreController.text) ?? sliderVal.toInt();
                context.read<StandaloneProvider>().toggleRecord(
                      taskId: widget.task.id,
                      studentId: student.id,
                      isDone: true,
                      score: score,
                      feedback: feedbackController.text.trim(),
                    );
                Navigator.of(ctx).pop();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('${student.name} uchun baho saqlandi! ✅'),
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

  void _confirmClearAll(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Belgilashlarni tozalash'),
        content: const Text(
          'Shu vazifa bo\'yicha barcha talabalarning "Bajarildi" belgisi, bahosi va izohi tozalanadi. Bu amalni ortga qaytarib bo\'lmaydi.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Bekor qilish')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () {
              context.read<StandaloneProvider>().batchMarkGroupTask(widget.task.id, widget.task.groupId, false);
              Navigator.of(ctx).pop();
            },
            child: const Text('Tozalash'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final prov = context.watch<StandaloneProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final group = prov.groups.where((g) => g.id == widget.task.groupId).firstOrNull;
    final students = group?.students ?? [];

    final completedCount = students.where((s) {
      final rec = prov.getRecord(widget.task.id, s.id);
      return rec != null && rec.isDone;
    }).length;

    final deadlineDate = DateTime.tryParse(widget.task.deadline);
    final deadlineStr = deadlineDate != null ? DateFormat('d MMM yyyy').format(deadlineDate) : widget.task.deadline;

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.task.title),
        actions: [
          IconButton(
            icon: const Icon(Icons.select_all_rounded),
            tooltip: 'Barchasiga Bajarildi qo\'yish',
            onPressed: () {
              prov.batchMarkGroupTask(widget.task.id, widget.task.groupId, true);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Barcha talabalarga "Bajarildi" belgilandi! ✅')),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Task Summary Card
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
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        widget.task.title,
                        style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Colors.white),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        'Maks: ${widget.task.maxScore} ball',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 12),
                      ),
                    ),
                  ],
                ),
                if (widget.task.description.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(
                    widget.task.description,
                    style: const TextStyle(color: Colors.white70, fontSize: 13),
                  ),
                ],
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Muddat: $deadlineStr',
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                    Text(
                      'Bajarildi: $completedCount / ${students.length}',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: students.isNotEmpty ? (completedCount / students.length) : 0.0,
                    minHeight: 6,
                    backgroundColor: Colors.white.withValues(alpha: 0.2),
                    valueColor: const AlwaysStoppedAnimation<Color>(Colors.greenAccent),
                  ),
                ),
              ],
            ),
          ),

          // Students Roster Grid / List for Rapid 1-Click Marking
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Talabalar (${students.length})',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
                  ),
                ),
                TextButton.icon(
                  onPressed: () => _confirmClearAll(context),
                  icon: const Icon(Icons.clear_all_rounded, size: 16, color: Colors.grey),
                  label: const Text('Tozalash', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 6),

          Expanded(
            child: students.isEmpty
                ? const Center(child: Text('Guruhda talabalar yo\'q. Avval talaba qo\'shing.'))
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
                    itemCount: students.length,
                    itemBuilder: (ctx, idx) {
                      final st = students[idx];
                      final rec = prov.getRecord(widget.task.id, st.id);
                      final isDone = rec != null && rec.isDone;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                          side: BorderSide(
                            color: isDone
                                ? AppColors.success.withValues(alpha: 0.5)
                                : (isDark ? AppColors.darkBorder : AppColors.lightBorder),
                            width: isDone ? 1.5 : 1,
                          ),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              CircleAvatar(
                                radius: 18,
                                backgroundColor:
                                    isDone ? AppColors.success.withValues(alpha: 0.15) : Colors.grey.withValues(alpha: 0.15),
                                child: Icon(
                                  isDone ? Icons.check_circle_rounded : Icons.person_outline_rounded,
                                  color: isDone ? AppColors.success : Colors.grey,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      st.name,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontWeight: FontWeight.w700,
                                        fontSize: 14.5,
                                        // Bajarmagan talaba ham xira emas, aniq ko'rinishi
                                        // kerak — aynan ular e'tibor talab qiladi.
                                        color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
                                      ),
                                    ),
                                    if (rec?.feedback != null && rec!.feedback!.isNotEmpty) ...[
                                      const SizedBox(height: 2),
                                      Text(
                                        'Izoh: ${rec.feedback!}',
                                        style: const TextStyle(fontSize: 11.5, color: Colors.grey),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                    ],
                                    if (isDone) ...[
                                      const SizedBox(height: 2),
                                      Text(
                                        'Baho: ${rec.score} ball',
                                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.primary),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                              const SizedBox(width: 4),
                              // Score / Edit button
                              IconButton(
                                visualDensity: VisualDensity.compact,
                                icon: const Icon(Icons.edit_note_rounded, color: AppColors.primary, size: 22),
                                tooltip: 'Baho va izoh kiritish',
                                onPressed: () => _openScoreDialog(context, st, rec),
                              ),
                              // 1-Click Done Toggle Button. "Belgilash" so'zi harakatni
                              // bildiradi — "Bajarmadi" avvalgi holatni ham, tugmani
                              // bosish harakatini ham anglatib chalkashtirar edi.
                              ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: isDone ? AppColors.success : (isDark ? AppColors.darkSurfaceElevated : Colors.grey.shade200),
                                  foregroundColor: isDone ? Colors.white : (isDark ? Colors.white70 : Colors.black87),
                                  elevation: 0,
                                  minimumSize: const Size(0, 36),
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                onPressed: () {
                                  prov.toggleRecord(
                                    taskId: widget.task.id,
                                    studentId: st.id,
                                    isDone: !isDone,
                                    score: !isDone ? widget.task.maxScore : 0,
                                    feedback: rec?.feedback,
                                  );
                                },
                                child: Text(
                                  isDone ? 'Bajarildi' : 'Belgilash',
                                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
                                ),
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
}
