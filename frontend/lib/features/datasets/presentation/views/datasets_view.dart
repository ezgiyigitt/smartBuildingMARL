import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../viewmodels/datasets_view_model.dart';

class DatasetsView extends ConsumerWidget {
  const DatasetsView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(datasetsViewModelProvider);
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Dataset registry', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
            'This page lists authorized sources. ASHRAE/Zenodo files are not bundled in git.',
          ),
          const SizedBox(height: 16),
          if (state.loading) const LinearProgressIndicator(),
          if (state.error != null) Text(state.error!),
          Expanded(
            child: ListView.builder(
              itemCount: state.records.length,
              itemBuilder: (context, index) {
                final item = state.records[index];
                return Card(
                  child: ListTile(
                    title: Text(item.title),
                    subtitle: Text(
                      'Status: ${item.status}\nRole: ${item.role}\n'
                      'Row-merge with CityLearn: ${item.mergeWithCitylearn}',
                    ),
                    isThreeLine: true,
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
