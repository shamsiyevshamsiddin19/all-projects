import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/custom_button.dart';
import '../../shared/widgets/custom_text_field.dart';
import '../assignments/assignment_provider.dart';

class SubmissionReviewModal extends StatefulWidget {
  final SubmissionModel submission;
  final int maxScore;

  const SubmissionReviewModal({
    super.key,
    required this.submission,
    required this.maxScore,
  });

  @override
  State<SubmissionReviewModal> createState() => _SubmissionReviewModalState();
}

class _SubmissionReviewModalState extends State<SubmissionReviewModal> {
  late TextEditingController _scoreController;
  final _feedbackController = TextEditingController();
  String _selectedDecision = "APPROVED"; // APPROVED, RESUBMIT, REJECTED
  double _scoreSlider = 0;

  @override
  void initState() {
    super.initState();
    final initialScore = widget.submission.latestScore ?? (widget.maxScore * 0.85).toInt();
    _scoreSlider = initialScore.toDouble();
    _scoreController = TextEditingController(text: "$initialScore");
    if (widget.submission.latestFeedback != null) {
      _feedbackController.text = widget.submission.latestFeedback!;
    }
  }

  @override
  void dispose() {
    _scoreController.dispose();
    _feedbackController.dispose();
    super.dispose();
  }

  void _onReview() async {
    final score = int.tryParse(_scoreController.text) ?? _scoreSlider.toInt();

    final assignProv = context.read<AssignmentProvider>();
    final success = await assignProv.gradeSubmission(
      submissionId: widget.submission.id,
      score: score,
      feedback: _feedbackController.text.trim(),
      decision: _selectedDecision,
    );

    if (!mounted) return;
    if (success) {
      Navigator.of(context).pop(true);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Baho va izoh muvaffaqiyatli saqlandi! 🎉"),
          backgroundColor: AppColors.success,
        ),
      );
    } else if (assignProv.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(assignProv.errorMessage!),
          backgroundColor: AppColors.danger,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final assignProv = context.watch<AssignmentProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: Container(
        decoration: BoxDecoration(
          color: Theme.of(context).cardTheme.color,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        ),
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 36,
                  height: 4,
                  decoration: BoxDecoration(color: Colors.grey.shade600, borderRadius: BorderRadius.circular(2)),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.submission.studentName ?? "Talaba",
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                        ),
                        Text(
                          widget.submission.studentEmail ?? "",
                          style: const TextStyle(fontSize: 12.5, color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                  if (widget.submission.isLate)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.danger.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text(
                        "Kechikkan",
                        style: TextStyle(color: AppColors.danger, fontSize: 11.5, fontWeight: FontWeight.w700),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 14),

              // Student's answer text box
              if (widget.submission.answerText != null && widget.submission.answerText!.isNotEmpty) ...[
                const Text("Talaba javobi:", style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.grey)),
                const SizedBox(height: 6),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.darkSurfaceElevated : AppColors.lightSurfaceElevated,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                  ),
                  child: Text(
                    widget.submission.answerText!,
                    style: const TextStyle(fontSize: 13.5),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Decision Chips
              const Text("Qaror:", style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.grey)),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildDecisionChip("APPROVED", "Qabul qilish", AppColors.success),
                  const SizedBox(width: 8),
                  _buildDecisionChip("RESUBMIT", "Qayta topshirish", AppColors.warning),
                  const SizedBox(width: 8),
                  _buildDecisionChip("REJECTED", "Rad etish", AppColors.danger),
                ],
              ),
              const SizedBox(height: 16),

              // Score Slider & Input
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("Baho (Ball):", style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
                  Text(
                    "${_scoreSlider.toInt()} / ${widget.maxScore}",
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppColors.primary),
                  ),
                ],
              ),
              Slider(
                value: _scoreSlider.clamp(0, widget.maxScore.toDouble()),
                min: 0,
                max: widget.maxScore.toDouble(),
                divisions: widget.maxScore,
                activeColor: AppColors.primary,
                onChanged: (val) {
                  setState(() {
                    _scoreSlider = val;
                    _scoreController.text = "${val.toInt()}";
                  });
                },
              ),
              const SizedBox(height: 8),

              // Feedback TextField
              CustomTextField(
                label: "O'qituvchi xulosasi (Feedback)",
                hint: "Masalan: A'lo bajarilgan! Lekin xatoliklarni qayta ko'rib chiqing.",
                controller: _feedbackController,
                maxLines: 3,
              ),
              const SizedBox(height: 24),

              CustomButton(
                text: "Baholashni Saqlash",
                onPressed: _onReview,
                isLoading: assignProv.isLoading,
                icon: Icons.check_rounded,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDecisionChip(String key, String label, Color color) {
    final isSelected = _selectedDecision == key;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (_) => setState(() => _selectedDecision = key),
      selectedColor: color,
      labelStyle: TextStyle(
        fontSize: 12,
        fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
        color: isSelected ? Colors.white : null,
      ),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      showCheckmark: false,
    );
  }
}
