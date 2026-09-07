import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../assignments/assignments_screen.dart';
import '../auth/auth_provider.dart';
import '../groups/groups_screen.dart';
import '../profile/profile_screen.dart';
import '../reports/reports_screen.dart';
import 'student_dashboard_view.dart';
import 'teacher_dashboard_view.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isTeacher = auth.user?.isTeacher ?? false;

    final List<Widget> screens = isTeacher
        ? const [
            TeacherDashboardView(),
            GroupsScreen(),
            AssignmentsScreen(),
            ReportsScreen(),
            ProfileScreen(),
          ]
        : const [
            StudentDashboardView(),
            AssignmentsScreen(),
            GroupsScreen(),
            ProfileScreen(),
          ];

    final List<BottomNavigationBarItem> navItems = isTeacher
        ? const [
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_outlined),
              activeIcon: Icon(Icons.dashboard_rounded),
              label: "Dashboard",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.groups_outlined),
              activeIcon: Icon(Icons.groups_rounded),
              label: "Guruhlar",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.assignment_outlined),
              activeIcon: Icon(Icons.assignment_rounded),
              label: "Vazifalar",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.bar_chart_rounded),
              activeIcon: Icon(Icons.insert_chart_rounded),
              label: "Hisobot",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline_rounded),
              activeIcon: Icon(Icons.person_rounded),
              label: "Profil",
            ),
          ]
        : const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined),
              activeIcon: Icon(Icons.home_rounded),
              label: "Asosiy",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.task_alt_outlined),
              activeIcon: Icon(Icons.task_alt_rounded),
              label: "Vazifalar",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.groups_outlined),
              activeIcon: Icon(Icons.groups_rounded),
              label: "Guruhlar",
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline_rounded),
              activeIcon: Icon(Icons.person_rounded),
              label: "Profil",
            ),
          ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (idx) => setState(() => _currentIndex = idx),
        items: navItems,
      ),
    );
  }
}
