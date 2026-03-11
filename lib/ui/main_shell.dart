import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:window_manager/window_manager.dart';

import '../overlay/overlay_window_manager.dart';
import '../providers/app_providers.dart';
import 'pages/debug_page.dart';
import 'pages/detail_config_page.dart';
import 'pages/settings_page.dart';
import 'pages/subtitle_settings_page.dart';
import 'pages/suggestion_page.dart';
import 'pages/translation_page.dart';

final _selectedIndexProvider = StateProvider<int>((ref) => 0);

class MainShell extends ConsumerStatefulWidget {
  const MainShell({super.key});

  @override
  ConsumerState<MainShell> createState() => _MainShellState();
}

class _MainShellState extends ConsumerState<MainShell> with WindowListener {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      setupMainWindowMethodHandler(ref);
      createOverlayWindow(ref);
    });
    windowManager.addListener(this);
  }

  @override
  void dispose() {
    windowManager.removeListener(this);
    super.dispose();
  }

  @override
  void onWindowClose() {
    closeOverlayWindow(ref);
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(realtimeStateProvider, (prev, next) {
      final segs = next.segments;
      if (segs.isNotEmpty) {
        final last = segs.last;
        sendSubtitleUpdate(ref, last.transcriptionText, last.primaryTranslation);
      }
    });
    final selectedIndex = ref.watch(_selectedIndexProvider);
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            extended: true,
            minExtendedWidth: 180,
            leading: Padding(
              padding: const EdgeInsets.only(top: 16, bottom: 8),
              child: Text(
                '象胥',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Theme.of(context).colorScheme.primary,
                      fontWeight: FontWeight.w600,
                    ),
              ),
            ),
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.translate_outlined),
                selectedIcon: Icon(Icons.translate),
                label: Text('翻译信息'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.tune_outlined),
                selectedIcon: Icon(Icons.tune),
                label: Text('详细配置'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.subtitles_outlined),
                selectedIcon: Icon(Icons.subtitles),
                label: Text('字幕设置'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.lightbulb_outline),
                selectedIcon: Icon(Icons.lightbulb),
                label: Text('对话建议'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.settings_outlined),
                selectedIcon: Icon(Icons.settings),
                label: Text('设置'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.bug_report_outlined),
                selectedIcon: Icon(Icons.bug_report),
                label: Text('调试信息'),
              ),
            ],
            selectedIndex: selectedIndex,
            onDestinationSelected: (index) {
              ref.read(_selectedIndexProvider.notifier).state = index;
            },
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: IndexedStack(
              index: selectedIndex,
              children: const [
                TranslationPage(),
                DetailConfigPage(),
                SubtitleSettingsPage(),
                SuggestionPage(),
                SettingsPage(),
                DebugPage(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

