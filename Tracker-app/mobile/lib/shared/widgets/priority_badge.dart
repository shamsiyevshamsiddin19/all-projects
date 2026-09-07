import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

class PriorityBadge extends StatelessWidget {
  final String priority;

  const PriorityBadge({super.key, required this.priority});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String label;

    switch (priority.toUpperCase()) {
      case "URGENT":
        bg = AppColors.danger.withValues(alpha: 0.15);
        fg = AppColors.danger;
        label = "Shoshilinch";
        break;
      case "HIGH":
        bg = AppColors.warning.withValues(alpha: 0.15);
        fg = AppColors.warning;
        label = "Yuqori";
        break;
      case "LOW":
        bg = AppColors.info.withValues(alpha: 0.15);
        fg = AppColors.info;
        label = "Past";
        break;
      case "MEDIUM":
      default:
        bg = AppColors.success.withValues(alpha: 0.15);
        fg = AppColors.success;
        label = "O'rtacha";
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: fg.withValues(alpha: 0.3), width: 0.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(color: fg, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(color: fg, fontSize: 11.5, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}
