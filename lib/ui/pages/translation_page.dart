import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/realtime_segment.dart';
import '../../providers/app_providers.dart';

class TranslationPage extends ConsumerWidget {
  const TranslationPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final realtimeState = ref.watch(realtimeStateProvider);
    final settings = ref.watch(appSettingsProvider);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: Card(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: realtimeState.segments.length,
                  itemBuilder: (context, index) {
                    final seg = realtimeState.segments[index];
                    return _SegmentTile(segment: seg);
                  },
                ),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Center(
            child: settings.when(
              data: (s) => _ControlButton(apiKey: s.apiKey),
              loading: () => const CircularProgressIndicator(),
              error: (e, st) => _ControlButton(apiKey: ''),
            ),
          ),
        ],
      ),
    );
  }
}

class _SegmentTile extends StatelessWidget {
  const _SegmentTile({required this.segment});

  final RealtimeSegment segment;

  @override
  Widget build(BuildContext context) {
    final isFinal = segment.isFinal;
    final colorScheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (segment.transcriptionText.isNotEmpty)
            Text(
              segment.transcriptionText,
              style: TextStyle(
                color: isFinal ? colorScheme.onSurface : colorScheme.onSurfaceVariant,
                fontStyle: isFinal ? FontStyle.normal : FontStyle.italic,
                fontSize: 15,
              ),
            ),
          if (segment.primaryTranslation.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              segment.primaryTranslation,
              style: TextStyle(
                color: isFinal ? colorScheme.primary : colorScheme.onSurfaceVariant,
                fontStyle: isFinal ? FontStyle.normal : FontStyle.italic,
                fontSize: 14,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _ControlButton extends ConsumerWidget {
  const _ControlButton({required this.apiKey});

  final String apiKey;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final realtimeState = ref.watch(realtimeStateProvider);
    final isRunning = realtimeState.sessionState == RealtimeSessionState.running ||
        realtimeState.sessionState == RealtimeSessionState.connecting ||
        realtimeState.sessionState == RealtimeSessionState.stopping;

    final controller = ref.read(realtimeControllerProvider);
    return FilledButton.icon(
      onPressed: () async {
        if (isRunning) {
          await controller.stop();
        } else {
          if (apiKey.isEmpty) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('请先在设置中配置 API Key')),
            );
            return;
          }
          await controller.start();
        }
      },
      icon: Icon(isRunning ? Icons.stop : Icons.mic),
      label: Text(isRunning ? '停止' : '开始识别与翻译'),
      style: FilledButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        textStyle: const TextStyle(fontSize: 16),
      ),
    );
  }
}
