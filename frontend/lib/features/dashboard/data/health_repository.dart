import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../domain/entities/health_status.dart';

final healthRepositoryProvider = Provider<HealthRepository>((ref) {
  return HealthRepository();
});

class HealthRepository {
  HealthRepository({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<HealthStatus> fetchHealth() async {
    try {
      final json = await _client.getJson('/api/health');
      return HealthStatus.fromJson(json);
    } catch (error) {
      return HealthStatus.unreachable(
        'Backend is not reachable at the configured API URL. Start FastAPI separately. ($error)',
      );
    }
  }
}
