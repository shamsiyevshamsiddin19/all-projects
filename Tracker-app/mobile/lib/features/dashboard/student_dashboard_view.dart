import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/stat_card.dart';
import '../assignments/assignment_provider.dart';
import '../auth/auth_provider.dart';
import '../groups/group_provider.dart';
import '../reports/analytics_provider.dart';

class StudentDashboardView extends StatefulWidget {
  const StudentDashboardView({super.key});

  @override
  State<StudentDashboardView> createState() => _StudentDashboardViewState();
}

class _StudentDashboardViewState extends State<StudentDashboardView> {
  final _inviteCodeController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalyticsProvider>().fetchDashboardStats();
      context.read<AssignmentProvider>().fetchAssignments();
    });
  }

  @override
  void dispose() {
    _inviteCodeController.dispose();
    super.dispose();
  }

  void _showJoinGroupDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text("Guruhga qo'shilish"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "O'qituvchingiz bergan 6 xonali taklif kodini kiriting:",
              style: TextStyle(fontSize: 13, color: Colors.grey),
            ),
            const SizedBox(height: 14),
            TextField(
              controller: _inviteCodeController,
              textCapitalization: TextCapitalization.characters,
              maxLength: 6,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, letterSpacing: 4),
              textAlign: TextAlign.center,
              decoration: InputDecoration(
                hintText: "ABC123",
                counterText: "",
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text("Bekor qilish"),
          ),
          ElevatedButton(
            onPressed: () async {
              final code = _inviteCodeController.text.trim();
              if (code.length < 4) return;

              Navigator.of(ctx).pop();
              final success = await context.read<GroupProvider>().joinGroup(code);
              if (mounted) {
                if (success) {
                  _inviteCodeController.clear();
                  context.read<AssignmentProvider>().fetchAssignments();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Guruhga muvaffaqiyatli qo'shildingiz! 🎉"),
                      backgroundColor: AppColors.success,
                    ),
                  );
                } else {
                  final err = context.read<GroupProvider>().errorMessage;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(err ?? "Guruhga ulanishda xatolik"),
                      backgroundColor: AppColors.danger,
                    ),
                  );
                }
              }
            },
            child: const Text("Qo'shilish"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final analytics = context.watch<AnalyticsProvider>();
    final stats = analytics.stats;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Salom, ${auth.user?.fullName ?? 'Talaba'}!",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
            ),
            const Text(
              "O'quvchi boshqaruv paneli",
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.group_add_rounded),
            tooltip: "Guruhga qo'shilish",
            onPressed: _showJoinGroupDialog,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          await context.read<AnalyticsProvider>().fetchDashboardStats();
          await context.read<AssignmentProvider>().fetchAssignments();
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Join Group Banner
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.vpn_key_rounded, color: Colors.white, size: 22),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Yangi guruhga qo'shiling",
                            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
                          ),
                          SizedBox(height: 2),
                          Text(
                            "O'qituvchi taklif kodi orqali",
                            style: TextStyle(color: Colors.white70, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton(
                      onPressed: _showJoinGroupDialog,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: AppColors.primaryDark,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                      ),
                      child: const Text("Kod kiritish"),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // 3 Metric Cards
              Row(
                children: [
                  Expanded(
                    child: StatCard(
                      title: "Faol Vazifalar",
                      value: "${stats?.activeTasks ?? 0}",
                      icon: Icons.assignment_late_outlined,
                      iconColor: AppColors.warning,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: StatCard(
                      title: "Topshirilgan",
                      value: "${stats?.completedTasks ?? 0}",
                      icon: Icons.task_alt_rounded,
                      iconColor: AppColors.success,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: StatCard(
                      title: "O'rtacha Ball",
                      value: "${stats?.averageScore ?? 0}",
                      icon: Icons.star_border_rounded,
                      iconColor: AppColors.primary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Progress Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            "Umumiy O'zlashtirish",
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                          ),
                          Text(
                            "${stats?.completionRate ?? 0}%",
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: AppColors.success,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: LinearProgressIndicator(
                          value: (stats?.completionRate ?? 0) / 100.0,
                          minHeight: 8,
                          backgroundColor: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                          valueColor: const AlwaysStoppedAnimation<Color>(AppColors.success),
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        "${stats?.completedTasks ?? 0} ta vazifa bajarilgan, ${stats?.overdueTasks ?? 0} ta muddat o'tgan.",
                        style: const TextStyle(fontSize: 12, color: Colors.grey),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Weekly Activity Progress
              Text(
                "Haftalik Faolligingiz",
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
                ),
              ),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 20, 20, 16),
                  child: SizedBox(
                    height: 160,
                    child: (stats?.weeklyActivity.isEmpty ?? true)
                        ? const Center(child: Text("Hozircha topshiriqlar faolligi yo'q"))
                        : LineChart(
                            LineChartData(
                              gridData: const FlGridData(show: false),
                              titlesData: FlTitlesData(
                                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                                bottomTitles: AxisTitles(
                                  sideTitles: SideTitles(
                                    showTitles: true,
                                    getTitlesWidget: (val, meta) {
                                      int idx = val.toInt();
                                      if (idx >= 0 && idx < stats!.weeklyActivity.length) {
                                        return Padding(
                                          padding: const EdgeInsets.only(top: 6),
                                          child: Text(
                                            stats.weeklyActivity[idx].label,
                                            style: const TextStyle(fontSize: 11, color: Colors.grey),
                                          ),
                                        );
                                      }
                                      return const SizedBox();
                                    },
                                  ),
                                ),
                              ),
                              borderData: FlBorderData(show: false),
                              lineBarsData: [
                                LineChartBarData(
                                  spots: stats!.weeklyActivity.asMap().entries.map((e) {
                                    return FlSpot(e.key.toDouble(), e.value.value.toDouble());
                                  }).toList(),
                                  isCurved: true,
                                  color: AppColors.success,
                                  barWidth: 3,
                                  isStrokeCapRound: true,
                                  dotData: const FlDotData(show: true),
                                  belowBarData: BarAreaData(
                                    show: true,
                                    color: AppColors.success.withValues(alpha: 0.15),
                                  ),
                                ),
                              ],
                            ),
                          ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
