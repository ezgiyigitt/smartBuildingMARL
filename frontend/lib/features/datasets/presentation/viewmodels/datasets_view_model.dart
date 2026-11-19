import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/dataset_repository.dart';
import '../../domain/entities/dataset_record.dart';

class DatasetsState {
  const DatasetsState({
    this.loading = true,
    this.records = const [],
    this.error,
  });

  final bool loading;
  final List<DatasetRecord> records;
  final String? error;
}

class DatasetsViewModel extends Notifier<DatasetsState> {
  DatasetsViewModel({DatasetRepository? repository})
    : _repository = repository ?? DatasetRepository();

  final DatasetRepository _repository;

  @override
  DatasetsState build() {
    Future.microtask(refresh);
    return const DatasetsState();
  }

  Future<void> refresh() async {
    state = const DatasetsState(loading: true);
    try {
      final records = await _repository.listDatasets();
      state = DatasetsState(loading: false, records: records);
    } catch (error) {
      state = DatasetsState(
        loading: false,
        error:
            'Cannot list datasets. Start the FastAPI backend first. ($error)',
      );
    }
  }
}

final datasetsViewModelProvider =
    NotifierProvider<DatasetsViewModel, DatasetsState>(DatasetsViewModel.new);
