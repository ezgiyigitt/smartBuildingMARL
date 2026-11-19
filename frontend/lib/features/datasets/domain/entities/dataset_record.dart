class DatasetRecord {
  const DatasetRecord({
    required this.id,
    required this.title,
    required this.role,
    required this.status,
    required this.mergeWithCitylearn,
    this.caveat,
  });

  final String id;
  final String title;
  final String role;
  final String status;
  final bool mergeWithCitylearn;
  final String? caveat;

  factory DatasetRecord.fromJson(Map<String, dynamic> json) {
    return DatasetRecord(
      id: json['id'] as String,
      title: json['title'] as String,
      role: json['role'] as String,
      status: json['status'] as String,
      mergeWithCitylearn: json['merge_with_citylearn'] as bool? ?? false,
      caveat: json['scientific_caveat'] as String?,
    );
  }
}
