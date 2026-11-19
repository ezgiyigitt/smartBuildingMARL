import '../../../core/network/api_client.dart';
import '../domain/entities/dataset_record.dart';

class DatasetRepository {
  DatasetRepository({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  Future<List<DatasetRecord>> listDatasets() async {
    final payload = await _client.getList('/api/datasets');
    return payload
        .whereType<Map<String, dynamic>>()
        .map(DatasetRecord.fromJson)
        .toList();
  }
}
