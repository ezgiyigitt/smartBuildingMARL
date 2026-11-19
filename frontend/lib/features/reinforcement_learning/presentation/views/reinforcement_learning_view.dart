import '../../../../core/widgets/status_page.dart';

class ReinforcementLearningView extends StatusPage {
  const ReinforcementLearningView({super.key})
    : super(
        title: 'Reinforcement learning training',
        body:
            'Training jobs will run asynchronously on the backend. '
            'This view will not block the UI or execute RL locally.',
      );
}
