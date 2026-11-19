import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_building_marl/app/app.dart';
import 'package:smart_building_marl/features/dashboard/data/health_repository.dart';
import 'package:smart_building_marl/features/dashboard/domain/entities/health_status.dart';

class _FakeHealthRepository extends HealthRepository {
  @override
  Future<HealthStatus> fetchHealth() async {
    return const HealthStatus(
      status: 'ok',
      citylearnPin: '3.5.0',
      pythonOk: true,
      message: 'Research API skeleton. No trained models or experimental results are served.',
      reachable: true,
    );
  }
}

void main() {
  testWidgets('dashboard shows research title', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthRepositoryProvider.overrideWithValue(_FakeHealthRepository()),
        ],
        child: const SmartBuildingApp(),
      ),
    );
    await tester.pump();
    expect(
      find.textContaining('Occupant-Aware, Uncertainty-Calibrated Safe MARL'),
      findsOneWidget,
    );
    expect(find.textContaining('does not control HVAC'), findsOneWidget);
  });
}
