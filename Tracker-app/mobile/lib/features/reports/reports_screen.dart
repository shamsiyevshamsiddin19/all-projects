import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../groups/group_provider.dart';
import 'analytics_provider.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  String? _selectedGroupId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GroupProvider>().fetchGroups();
      context.read<AnalyticsProvider>().fetchDashboardStats();
    });
  }

  void _exportPdf() async {
    final analytics = context.read<AnalyticsProvider>();
    final path = await analytics.exportReportPdf(groupId: _selectedGroupId);
    if (!mounted) return;
    if (path != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("PDF hisobot tayyorlandi: $path"),
          backgroundColor: AppColors.success,
        ),
      );
    } else if (analytics.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(analytics.errorMessage!), backgroundColor: AppColors.danger),
      );
    }
  }

  void _exportExcel() async {
    final analytics = context.read<AnalyticsProvider>();
    final path = await analytics.exportReportExcel(groupId: _selectedGroupId);
    if (!mounted) return;
    if (path != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("Excel hisobot tayyorlandi: $path"),
          backgroundColor: AppColors.success,
        ),
      );
    } else if (analytics.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(analytics.errorMessage!), backgroundColor: AppColors.danger),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final groupProv = context.watch<GroupProvider>();
    final analytics = context.watch<AnalyticsProvider>();
    final stats = analytics.stats;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Tahliliy Hisobotlar"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Filter card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Hisobot parametrlarini tanlang",
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: _selectedGroupId,
                      decoration: InputDecoration(
                        labelText: "Guruh",
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      items: [
                        const DropdownMenuItem(value: null, child: Text("Barcha Guruhlar")),
                        ...groupProv.groups.map((g) => DropdownMenuItem(value: g.id, child: Text(g.name))),
                      ],
                      onChanged: (val) => setState(() => _selectedGroupId = val),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Export Actions
            Text(
              "Eksport Formatlari",
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: isDark ? AppColors.darkTextPrimary : AppColors.lightTextPrimary,
              ),
            ),
            const SizedBox(height: 12),

            // PDF Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.danger.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.picture_as_pdf_rounded, color: AppColors.danger, size: 28),
                    ),
                    const SizedBox(width: 16),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("PDF Hisobot", style: TextStyle(fontSize: 15.5, fontWeight: FontWeight.w700)),
                          SizedBox(height: 2),
                          Text("Rasmiy ko'rinishdagi jadval va ko'rsatkichlar", style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                    ),
                    ElevatedButton.icon(
                      onPressed: analytics.isExporting ? null : _exportPdf,
                      icon: const Icon(Icons.download_rounded, size: 16),
                      label: const Text("Yuklash"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.danger,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Excel Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.success.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.table_chart_rounded, color: AppColors.success, size: 28),
                    ),
                    const SizedBox(width: 16),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text("Excel (XLSX) Hisobot", style: TextStyle(fontSize: 15.5, fontWeight: FontWeight.w700)),
                          SizedBox(height: 2),
                          Text("To'liq tahrirlanuvchi ma'lumotlar jadvali", style: TextStyle(fontSize: 12, color: Colors.grey)),
                        ],
                      ),
                    ),
                    ElevatedButton.icon(
                      onPressed: analytics.isExporting ? null : _exportExcel,
                      icon: const Icon(Icons.download_rounded, size: 16),
                      label: const Text("Yuklash"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.success,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Report Preview Summary
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Hisobot Xulosasi Ko'rinishi",
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 14),
                    _buildRow("Jami talabalar:", "${stats?.totalStudents ?? 0} nafar"),
                    const Divider(height: 16),
                    _buildRow("O'rtacha ball:", "${stats?.averageScore ?? 0} / 100"),
                    const Divider(height: 16),
                    _buildRow("O'zlashtirish foizi:", "${stats?.completionRate ?? 0}%"),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String val) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13.5, color: Colors.grey)),
        Text(val, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
      ],
    );
  }
}
