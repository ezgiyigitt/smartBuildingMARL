import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class ResearchShell extends StatelessWidget {
  const ResearchShell({super.key, required this.child});

  final Widget child;

  static const _items = [
    _NavItem(label: 'Dashboard', path: '/', icon: Icons.space_dashboard_outlined),
    _NavItem(label: 'Datasets', path: '/datasets', icon: Icons.storage_outlined),
    _NavItem(label: 'Thermal analysis', path: '/comfort', icon: Icons.thermostat_outlined),
    _NavItem(label: 'Occupancy', path: '/occupancy', icon: Icons.groups_outlined),
    _NavItem(label: 'Experiments', path: '/experiments', icon: Icons.tune_outlined),
    _NavItem(label: 'Training', path: '/training', icon: Icons.model_training_outlined),
    _NavItem(label: 'Results', path: '/results', icon: Icons.bar_chart_outlined),
    _NavItem(label: 'Reports', path: '/reports', icon: Icons.description_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _indexFor(location),
            onDestinationSelected: (index) => context.go(_items[index].path),
            labelType: NavigationRailLabelType.all,
            destinations: [
              for (final item in _items)
                NavigationRailDestination(
                  icon: Icon(item.icon),
                  label: Text(item.label),
                ),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(child: child),
        ],
      ),
    );
  }

  int _indexFor(String location) {
    final match = _items.indexWhere(
      (item) => item.path != '/' && location.startsWith(item.path),
    );
    return match == -1 ? 0 : match;
  }
}

class _NavItem {
  const _NavItem({required this.label, required this.path, required this.icon});

  final String label;
  final String path;
  final IconData icon;
}
