import '../../../../core/widgets/status_page.dart';

class ResultsView extends StatusPage {
  const ResultsView({super.key})
    : super(
        title: 'Results and comparisons',
        body:
            'Comparison charts bind only to stored experiment metrics. No runs exist yet.',
      );
}
