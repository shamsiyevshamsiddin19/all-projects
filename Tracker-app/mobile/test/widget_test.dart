import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:tracker_app/features/assignments/assignment_provider.dart';
import 'package:tracker_app/features/auth/auth_provider.dart';
import 'package:tracker_app/features/groups/group_provider.dart';
import 'package:tracker_app/features/reports/analytics_provider.dart';
import 'package:tracker_app/features/standalone/standalone_provider.dart';
import 'package:tracker_app/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => StandaloneProvider()),
          ChangeNotifierProvider(create: (_) => AuthProvider()),
          ChangeNotifierProvider(create: (_) => GroupProvider()),
          ChangeNotifierProvider(create: (_) => AssignmentProvider()),
          ChangeNotifierProvider(create: (_) => AnalyticsProvider()),
        ],
        child: const TrackerApp(),
      ),
    );

    expect(find.byType(TrackerApp), findsOneWidget);
  });
}
