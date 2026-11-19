import 'package:flutter_test/flutter_test.dart';
import 'package:smart_building_marl/features/datasets/domain/entities/dataset_record.dart';

void main() {
  test('dataset entity keeps merge flag false when omitted', () {
    final record = DatasetRecord.fromJson({
      'id': 'ashrae_gcdb2',
      'title': 'ASHRAE',
      'role': 'tsv',
      'status': 'not_downloaded',
    });
    expect(record.mergeWithCitylearn, isFalse);
  });
}
