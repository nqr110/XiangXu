import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/app_settings.dart';
import '../../models/audio_source.dart';
import '../../providers/app_providers.dart';

class DetailConfigPage extends ConsumerWidget {
  const DetailConfigPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(appSettingsProvider);

    return settings.when(
      data: (s) => _DetailConfigBody(settings: s),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('加载配置失败: $e')),
    );
  }
}

class _DetailConfigBody extends ConsumerWidget {
  const _DetailConfigBody({required this.settings});

  final AppSettings settings;

  static const List<({RecognitionMode mode, String label})> modeOptions = [
    (mode: RecognitionMode.recognitionOnly, label: '仅识别'),
    (mode: RecognitionMode.translationOnly, label: '仅翻译'),
    (mode: RecognitionMode.both, label: '同时识别与翻译'),
  ];

  static const Map<String, String> sourceLanguages = {
    'auto': '自动',
    'zh': '中文',
    'en': '英文',
    'ja': '日语',
    'ko': '韩语',
    'yue': '粤语',
    'de': '德语',
    'fr': '法语',
    'ru': '俄语',
    'it': '意大利语',
    'es': '西班牙语',
  };

  static const Map<String, String> targetLanguages = {
    'zh': '中文',
    'en': '英文',
    'ja': '日语',
    'ko': '韩语',
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '识别/翻译模式',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          SegmentedButton<RecognitionMode>(
            segments: modeOptions
                .map((e) => ButtonSegment<RecognitionMode>(
                      value: e.mode,
                      label: Text(e.label),
                    ))
                .toList(),
            selected: {settings.recognitionMode},
            onSelectionChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch((s) => s.copyWith(recognitionMode: v.first));
            },
          ),
          const SizedBox(height: 24),
          Text(
            '源语言',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: settings.sourceLanguage,
            decoration: const InputDecoration(
              isDense: true,
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            ),
            items: sourceLanguages.entries
                .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                .toList(),
            onChanged: (v) {
              if (v != null) {
                ref.read(appSettingsProvider.notifier).patch((s) => s.copyWith(sourceLanguage: v));
              }
            },
          ),
          const SizedBox(height: 16),
          Text(
            '目标语言',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: settings.targetLanguage,
            decoration: const InputDecoration(
              isDense: true,
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            ),
            items: targetLanguages.entries
                .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                .toList(),
            onChanged: (v) {
              if (v != null) {
                ref.read(appSettingsProvider.notifier).patch((s) => s.copyWith(targetLanguage: v));
              }
            },
          ),
          const SizedBox(height: 24),
          Text(
            '声音来源',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: settings.audioSourceId ?? AudioSource.systemMixId,
            decoration: const InputDecoration(
              isDense: true,
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            ),
            items: [
              DropdownMenuItem(
                value: AudioSource.systemMixId,
                child: Text(AudioSource.systemMix.displayName),
              ),
            ],
            onChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch((s) => s.copyWith(audioSourceId: v));
            },
          ),
        ],
      ),
    );
  }
}
