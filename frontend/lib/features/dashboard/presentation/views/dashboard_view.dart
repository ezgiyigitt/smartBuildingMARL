import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../viewmodels/dashboard_view_model.dart';

class DashboardView extends ConsumerWidget {
  const DashboardView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(dashboardViewModelProvider);
    final health = state.health;
    return Padding(
      padding: const EdgeInsets.all(32),
      child: ListView(
        children: [
          Text(
            'Occupant-Aware, Uncertainty-Calibrated Safe MARL',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          const Text(
            'Simulation research environment. This dashboard does not control HVAC equipment.',
          ),
          const SizedBox(height: 24),
          if (state.loading)
            const LinearProgressIndicator()
          else if (health == null)
            const Text('No backend status loaded.')
          else
            Card(
              child: ListTile(
                title: Text('API status: ${health.status}'),
                subtitle: Text(
                  'CityLearn pin: ${health.citylearnPin}\n${health.message}',
                ),
                trailing: Icon(
                  health.reachable ? Icons.check_circle_outline : Icons.error_outline,
                ),
              ),
            ),
          const SizedBox(height: 16),
          const Text(
            'Dataset files, trained models, and experiment metrics: not available until later phases produce artifacts.',
          ),
        ],
      ),
    );
  }
}
