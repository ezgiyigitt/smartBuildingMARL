import '../../../../core/widgets/status_page.dart';

class ExperimentsView extends StatusPage {
  const ExperimentsView({super.key})
    : super(
        title: 'Experiment configuration',
        body:
            'Configuration UI is deferred until a compatible CityLearn schema is inspected in Phase 5. '
            'Reward weights remain unset until sensitivity analysis.',
      );
}
