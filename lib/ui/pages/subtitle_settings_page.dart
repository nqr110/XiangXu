import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/app_settings.dart';
import '../../overlay/overlay_window_manager.dart';
import '../../providers/app_providers.dart';

class SubtitleSettingsPage extends ConsumerWidget {
  const SubtitleSettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(appSettingsProvider);

    return settings.when(
      data: (s) => _SubtitleSettingsBody(subtitle: s.subtitle),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('加载失败: $e')),
    );
  }
}

class _SubtitleSettingsBody extends ConsumerWidget {
  const _SubtitleSettingsBody({required this.subtitle});

  final SubtitleWindowSettings subtitle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SwitchListTile(
            title: const Text('启用字幕小窗'),
            value: subtitle.enabled,
            onChanged: (v) async {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(enabled: v)),
                  );
              if (v) {
                await createOverlayWindow(ref);
              } else {
                await closeOverlayWindow(ref);
              }
            },
          ),
          SwitchListTile(
            title: const Text('前置模式'),
            subtitle: const Text('小窗保持在前端'),
            value: subtitle.alwaysOnTop,
            onChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(alwaysOnTop: v)),
                  );
              sendSubtitleSettingsToOverlay(ref);
            },
          ),
          SwitchListTile(
            title: const Text('透传模式'),
            subtitle: const Text('鼠标穿透，防止误触'),
            value: subtitle.clickThrough,
            onChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(clickThrough: v)),
                  );
              sendSubtitleSettingsToOverlay(ref);
            },
          ),
          const SizedBox(height: 8),
          Text('圆角弧度', style: Theme.of(context).textTheme.titleSmall),
          Slider(
            value: subtitle.cornerRadius,
            min: 0,
            max: 32,
            divisions: 16,
            label: '${subtitle.cornerRadius.round()}',
            onChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(cornerRadius: v)),
                  );
              sendSubtitleSettingsToOverlay(ref);
            },
          ),
          const SizedBox(height: 8),
          Text('背景透明度', style: Theme.of(context).textTheme.titleSmall),
          Slider(
            value: subtitle.backgroundOpacity,
            min: 0.2,
            max: 1,
            onChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(backgroundOpacity: v)),
                  );
              sendSubtitleSettingsToOverlay(ref);
            },
          ),
          Text('文字透明度', style: Theme.of(context).textTheme.titleSmall),
          Slider(
            value: subtitle.textOpacity,
            min: 0.5,
            max: 1,
            onChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(textOpacity: v)),
                  );
              sendSubtitleSettingsToOverlay(ref);
            },
          ),
          const SizedBox(height: 8),
          Text('字幕位置', style: Theme.of(context).textTheme.titleSmall),
          SegmentedButton<SubtitleAlignmentMode>(
            segments: [
              ButtonSegment<SubtitleAlignmentMode>(value: SubtitleAlignmentMode.left, label: const Text('左')),
              ButtonSegment<SubtitleAlignmentMode>(value: SubtitleAlignmentMode.center, label: const Text('中')),
              ButtonSegment<SubtitleAlignmentMode>(value: SubtitleAlignmentMode.right, label: const Text('右')),
              ButtonSegment<SubtitleAlignmentMode>(value: SubtitleAlignmentMode.split, label: const Text('拆分')),
            ],
            selected: {subtitle.alignmentMode},
            onSelectionChanged: (v) {
              ref.read(appSettingsProvider.notifier).patch(
                    (s) => s.copyWith(subtitle: s.subtitle.copyWith(alignmentMode: v.first)),
                  );
              sendSubtitleSettingsToOverlay(ref);
            },
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              SizedBox(
                width: 120,
                child: TextFormField(
                  initialValue: '${subtitle.width.round()}',
                  decoration: const InputDecoration(labelText: '宽度'),
                  keyboardType: TextInputType.number,
                  onChanged: (v) {
                    final n = double.tryParse(v);
                    if (n != null && n >= 200 && n <= 1600) {
                      ref.read(appSettingsProvider.notifier).patch(
                            (s) => s.copyWith(subtitle: s.subtitle.copyWith(width: n)),
                          );
                      sendSubtitleSettingsToOverlay(ref);
                    }
                  },
                ),
              ),
              const SizedBox(width: 16),
              SizedBox(
                width: 120,
                child: TextFormField(
                  initialValue: '${subtitle.height.round()}',
                  decoration: const InputDecoration(labelText: '高度'),
                  keyboardType: TextInputType.number,
                  onChanged: (v) {
                    final n = double.tryParse(v);
                    if (n != null && n >= 80 && n <= 500) {
                      ref.read(appSettingsProvider.notifier).patch(
                            (s) => s.copyWith(subtitle: s.subtitle.copyWith(height: n)),
                          );
                      sendSubtitleSettingsToOverlay(ref);
                    }
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
