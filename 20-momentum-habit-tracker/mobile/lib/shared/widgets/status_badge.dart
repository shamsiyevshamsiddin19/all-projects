import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class StatusBadge extends StatelessWidget {
  final String status;
  final bool isLate;

  const StatusBadge({super.key, required this.status, this.isLate = false});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String label;

    if (isLate) {
      bg = AppColors.danger.withValues(alpha: 0.15);
      fg = AppColors.danger;
      label = "Kechikkan";
    } else {
      switch (status.toUpperCase()) {
        case "GRADED":
          bg = AppColors.success.withValues(alpha: 0.15);
          fg = AppColors.success;
          label = "Baholandi";
          break;
        case "SUBMITTED":
          bg = AppColors.info.withValues(alpha: 0.15);
          fg = AppColors.info;
          label = "Topshirildi";
          break;
        case "RESUBMIT_REQUESTED":
          bg = AppColors.warning.withValues(alpha: 0.15);
          fg = AppColors.warning;
          label = "Qayta topshirish";
          break;
        case "PUBLISHED":
          bg = AppColors.primary.withValues(alpha: 0.15);
          fg = AppColors.primary;
          label = "Faol";
          break;
        case "DRAFT":
        default:
          bg = Colors.grey.withValues(alpha: 0.15);
          fg = Colors.grey;
          label = "Qoralama";
          break;
      }
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(color: fg, fontSize: 11.5, fontWeight: FontWeight.w600),
      ),
    );
  }
}
