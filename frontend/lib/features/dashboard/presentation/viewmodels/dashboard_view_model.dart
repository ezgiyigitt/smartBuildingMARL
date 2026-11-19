import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/health_repository.dart';
import '../../domain/entities/health_status.dart';

class DashboardState {
  const DashboardState({this.loading = true, this.health});

  final bool loading;
  final HealthStatus? health;

  DashboardState copyWith({bool? loading, HealthStatus? health}) {
    return DashboardState(
      loading: loading ?? this.loading,
      health: health ?? this.health,
    );
  }
}

class DashboardViewModel extends Notifier<DashboardState> {
  @override
  DashboardState build() {
    Future.microtask(refresh);
    return const DashboardState();
  }

  Future<void> refresh() async {
    state = state.copyWith(loading: true);
    final health = await ref.read(healthRepositoryProvider).fetchHealth();
    state = DashboardState(loading: false, health: health);
  }
}

final dashboardViewModelProvider =
    NotifierProvider<DashboardViewModel, DashboardState>(DashboardViewModel.new);
