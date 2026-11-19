import '../../../../core/widgets/status_page.dart';

class ComfortAnalysisView extends StatusPage {
  const ComfortAnalysisView({super.key})
    : super(
        title: 'Thermal sensation analysis',
        body:
            'Phase 3 will train TSV models on downloaded ASHRAE data. '
            'TSV is not displayed as measured thermal comfort.',
      );
}
