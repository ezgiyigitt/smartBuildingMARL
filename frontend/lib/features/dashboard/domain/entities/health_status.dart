class HealthStatus {
  const HealthStatus({
    required this.status,
    required this.citylearnPin,
    required this.pythonOk,
    required this.message,
    required this.reachable,
  });

  final String status;
  final String citylearnPin;
  final bool pythonOk;
  final String message;
  final bool reachable;

  factory HealthStatus.fromJson(Map<String, dynamic> json) {
    return HealthStatus(
      status: json['status'] as String? ?? 'unknown',
      citylearnPin: json['citylearn_pin'] as String? ?? 'unreported',
      pythonOk: json['python_ok'] as bool? ?? false,
      message: json['message'] as String? ?? '',
      reachable: true,
    );
  }

  factory HealthStatus.unreachable(String reason) {
    return HealthStatus(
      status: 'unreachable',
      citylearnPin: 'n/a',
      pythonOk: false,
      message: reason,
      reachable: false,
    );
  }
}
