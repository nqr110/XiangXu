import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/app_providers.dart';

class DebugPage extends ConsumerWidget {
  const DebugPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final logs = ref.watch(debugLogProvider);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                onPressed: () {
                  ref.read(debugLogProvider.notifier).clear();
                },
                icon: const Icon(Icons.clear_all, size: 18),
                label: const Text('清空'),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: () {
                  final text = logs.join('\n');
                  if (text.isNotEmpty) {
                    Clipboard.setData(ClipboardData(text: text));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('已复制到剪贴板')),
                    );
                  }
                },
                icon: const Icon(Icons.copy, size: 18),
                label: const Text('复制日志'),
                style: FilledButton.styleFrom(
                  backgroundColor: Theme.of(context).colorScheme.surfaceContainerHigh,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Expanded(
            child: Card(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  color: Theme.of(context).colorScheme.surfaceContainerLowest,
                  padding: const EdgeInsets.all(12),
                  child: ListView.builder(
                    itemCount: logs.length,
                    itemBuilder: (context, index) {
                      return SelectableText(
                        logs[index],
                        style: TextStyle(
                          fontFamily: 'Consolas',
                          fontSize: 12,
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
