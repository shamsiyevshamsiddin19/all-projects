import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/stat_card.dart';
import '../assignments/create_assignment_screen.dart';
import '../auth/auth_provider.dart';
import '../reports/analytics_provider.dart';

class TeacherDashboardView extends StatefulWidget {
  const TeacherDashboardView({super.key});

  @override
  State<TeacherDashboardView> createState() => _TeacherDashboardViewState();
}

class _TeacherDashboardViewState extends State<TeacherDashboardView> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalyticsProvider>().fetchDashboardStats();
    });
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
              "Salom, ${auth.user?.fullName ?? 'O\'qituvchi'}",
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
            ),
            const Text(
              "O'qituvchi boshqaruv paneli",
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => analytics.fetchDashboardStats(),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => analytics.fetchDashboardStats(),
        child: analytics.isLoading && stats == null
            ? const Center(child: CircularProgressIndicator())
            : SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Quick Action Banner
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [AppColors.primaryDark, AppColors.accent],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Yangi vazifa berish",
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                "Guruh yoki talabaga deadline bilan",
                                style: TextStyle(color: Colors.white70, fontSize: 12),
                              ),
                            ],
                          ),
                          ElevatedButton.icon(
                            onPressed: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => const CreateAssignmentScreen(),
                                ),
                              );
                            },
                            icon: const Icon(Icons.add, size: 18),
                            label: const Text("Yaratish"),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.white,
                              foregroundColor: AppColors.primaryDark,
                              elevation: 0,
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),

                    // 4 Grid Stat Cards
                    GridView.count(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      childAspectRatio: 1.35,
                      children: [
                        StatCard(
                          title: "Jami Talabalar",
                          value: "${stats?.totalStudents ?? 0}",
                          icon: Icons.people_alt_outlined,
                          iconColor: AppColors.info,
                        ),
                        StatCard(
                          title: "Faol Guruhlar",
                          value: "${stats?.totalGroups ?? 0}",
                          icon: Icons.folder_outlined,
                          iconColor: AppColors.primary,
                        ),
                        StatCard(
                          title: "Kutilayotgan Tekshiruvlar",
                          value: "${stats?.pendingReviews ?? 0}",
                          icon: Icons.pending_actions_rounded,
                          iconColor: AppColors.warning,
                        ),
                        StatCard(
                          title: "O'rtacha Ball",
                          value: "${stats?.averageScore ?? 0}/100",
                          icon: Icons.star_border_rounded,
                          iconColor: AppColors.success,
                          subtitle: "${stats?.completionRate ?? 0}% tugallangan",
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // Weekly Activity Chart
                    Text(
                      "Haftalik Topshiriqlar Faolligi",
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
                          height: 180,
                          child: (stats?.weeklyActivity.isEmpty ?? true)
                              ? const Center(child: Text("Hozircha ma'lumot yo'q"))
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
                                        color: AppColors.primary,
                                        barWidth: 3,
                                        isStrokeCapRound: true,
                                        dotData: const FlDotData(show: true),
                                        belowBarData: BarAreaData(
                                          show: true,
                                          color: AppColors.primary.withValues(alpha: 0.15),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Group Performance List
                    if (stats?.groupPerformances.isNotEmpty ?? false) ...[
                      Text(
                        "Guruhlar Bo'yicha O'zlashtirish",
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ...stats!.groupPerformances.map((g) => Card(
                            margin: const EdgeInsets.only(bottom: 10),
                            child: Padding(
                              padding: const EdgeInsets.all(14),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        g.groupName,
                                        style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14.5),
                                      ),
                                      Text(
                                        "${g.averageScore} ball",
                                        style: const TextStyle(
                                          fontWeight: FontWeight.w700,
                                          color: AppColors.primary,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  ClipRRect(
                                    borderRadius: BorderRadius.circular(6),
                                    child: LinearProgressIndicator(
                                      value: g.completionRate / 100.0,
                                      minHeight: 6,
                                      backgroundColor: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                                      valueColor: const AlwaysStoppedAnimation<Color>(AppColors.success),
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text("${g.totalStudents} ta talaba", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                      Text("${g.completionRate}% bajarildi", style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          )),
                    ],
                  ],
                ),
              ),
      ),
    );
  }
}
