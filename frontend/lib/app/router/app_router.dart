import 'package:go_router/go_router.dart';

import '../../core/widgets/research_shell.dart';
import '../../features/comfort_analysis/presentation/views/comfort_analysis_view.dart';
import '../../features/dashboard/presentation/views/dashboard_view.dart';
import '../../features/datasets/presentation/views/datasets_view.dart';
import '../../features/experiments/presentation/views/experiments_view.dart';
import '../../features/occupancy_forecasting/presentation/views/occupancy_forecasting_view.dart';
import '../../features/reinforcement_learning/presentation/views/reinforcement_learning_view.dart';
import '../../features/reports/presentation/views/reports_view.dart';
import '../../features/results/presentation/views/results_view.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) => ResearchShell(child: child),
      routes: [
        GoRoute(path: '/', builder: (context, state) => const DashboardView()),
        GoRoute(
          path: '/datasets',
          builder: (context, state) => const DatasetsView(),
        ),
        GoRoute(
          path: '/comfort',
          builder: (context, state) => const ComfortAnalysisView(),
        ),
        GoRoute(
          path: '/occupancy',
          builder: (context, state) => const OccupancyForecastingView(),
        ),
        GoRoute(
          path: '/experiments',
          builder: (context, state) => const ExperimentsView(),
        ),
        GoRoute(
          path: '/training',
          builder: (context, state) => const ReinforcementLearningView(),
        ),
        GoRoute(
          path: '/results',
          builder: (context, state) => const ResultsView(),
        ),
        GoRoute(
          path: '/reports',
          builder: (context, state) => const ReportsView(),
        ),
      ],
    ),
  ],
);
