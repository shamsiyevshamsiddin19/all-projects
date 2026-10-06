import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../auth/auth_provider.dart';
import '../auth/login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String _selectedLang = "UZ";

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    final isDark = auth.isDarkMode;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Profil va Sozlamalar"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          children: [
            // User Header Card
            Center(
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 42,
                    backgroundColor: AppColors.primary.withValues(alpha: 0.2),
                    child: Text(
                      user?.fullName.isNotEmpty == true ? user!.fullName[0].toUpperCase() : "U",
                      style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: AppColors.primary),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    user?.fullName ?? "Foydalanuvchi",
                    style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.email ?? "",
                    style: const TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      user?.isTeacher == true ? "O'qituvchi (Teacher)" : "Talaba (Student)",
                      style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w700, fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // Settings Group
            Card(
              child: Column(
                children: [
                  SwitchListTile(
                    secondary: Icon(
                      isDark ? Icons.dark_mode_rounded : Icons.light_mode_rounded,
                      color: AppColors.primary,
                    ),
                    title: const Text("Mavzu (Dark Mode)", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14.5)),
                    subtitle: Text(isDark ? "Qorong'u mavzu faol" : "Yorug' mavzu faol", style: const TextStyle(fontSize: 12)),
                    value: isDark,
                    onChanged: (val) => auth.toggleTheme(),
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.language_rounded, color: AppColors.primary),
                    title: const Text("Ilova tili", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14.5)),
                    trailing: DropdownButton<String>(
                      value: _selectedLang,
                      underline: const SizedBox(),
                      items: const [
                        DropdownMenuItem(value: "UZ", child: Text("O'zbekcha")),
                        DropdownMenuItem(value: "RU", child: Text("Русский")),
                        DropdownMenuItem(value: "EN", child: Text("English")),
                      ],
                      onChanged: (v) {
                        if (v != null) setState(() => _selectedLang = v);
                      },
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Security Card
            Card(
              child: Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.security_rounded, color: AppColors.primary),
                    title: const Text("Xavfsizlik & Parol", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14.5)),
                    trailing: const Icon(Icons.chevron_right_rounded, color: Colors.grey),
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("Parolni o'zgartirish sozlamalari")),
                      );
                    },
                  ),
                  const Divider(height: 1),
                  ListTile(
                    leading: const Icon(Icons.info_outline_rounded, color: AppColors.primary),
                    title: const Text("Loyiha haqida", style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14.5)),
                    subtitle: const Text("Teacher-Student Task Manager v1.0.0", style: TextStyle(fontSize: 12)),
                    trailing: const Icon(Icons.chevron_right_rounded, color: Colors.grey),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Logout Button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.danger),
                  foregroundColor: AppColors.danger,
                ),
                onPressed: () async {
                  await auth.logout();
                  if (mounted) {
                    Navigator.of(context).pushAndRemoveUntil(
                      MaterialPageRoute(builder: (_) => const LoginScreen()),
                      (route) => false,
                    );
                  }
                },
                icon: const Icon(Icons.logout_rounded, size: 18),
                label: const Text("Tizimdan Chiqish", style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
