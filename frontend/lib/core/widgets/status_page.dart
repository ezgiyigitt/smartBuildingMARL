import 'package:flutter/material.dart';

class StatusPage extends StatelessWidget {
  const StatusPage({
    super.key,
    required this.title,
    required this.body,
    this.footnote =
        'No experimental numbers are shown until artifacts exist on disk.',
  });

  final String title;
  final String body;
  final String footnote;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.all(32),
      child: ListView(
        children: [
          Text(title, style: theme.textTheme.headlineSmall),
          const SizedBox(height: 12),
          Text(body, style: theme.textTheme.bodyLarge),
          const SizedBox(height: 24),
          Text(footnote, style: theme.textTheme.bodySmall),
        ],
      ),
    );
  }
}
