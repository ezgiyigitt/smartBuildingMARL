import '../../../../core/widgets/status_page.dart';

class ReportsView extends StatusPage {
  const ReportsView({super.key})
    : super(
        title: 'Scientific reports',
        body:
            'Exports will copy dataset reports, evaluation files, and reproducibility metadata that already exist. '
            'This page will not generate fabricated results.',
      );
}
