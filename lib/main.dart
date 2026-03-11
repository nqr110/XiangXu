import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:window_manager/window_manager.dart';

import 'overlay/subtitle_overlay_app.dart';
import 'ui/main_shell.dart';

void main(List<String> args) async {
  WidgetsFlutterBinding.ensureInitialized();

  if (args.length >= 3 && args[0] == 'multi_window') {
    final windowId = int.parse(args[1]);
    final argument = args[2].isEmpty
        ? <String, dynamic>{}
        : jsonDecode(args[2]) as Map<String, dynamic>;
    runApp(SubtitleOverlayApp(windowId: windowId, args: argument));
    return;
  }

  await windowManager.ensureInitialized();
  const size = Size(1000, 700);
  const minSize = Size(800, 560);
  await windowManager.waitUntilReadyToShow(
    null,
    () async {
      await windowManager.setTitleBarStyle(TitleBarStyle.normal);
      await windowManager.setSize(size);
      await windowManager.setMinimumSize(minSize);
      await windowManager.center();
      await windowManager.show();
      await windowManager.focus();
    },
  );
  runApp(
    const ProviderScope(
      child: XiangXuApp(),
    ),
  );
}

class XiangXuApp extends StatelessWidget {
  const XiangXuApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '象胥 - 实时语音识别与翻译',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF5C6BC0), brightness: Brightness.light),
        cardTheme: CardThemeData(
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          margin: const EdgeInsets.all(0),
        ),
        navigationRailTheme: const NavigationRailThemeData(
          labelType: NavigationRailLabelType.none,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            elevation: 0,
          ),
        ),
      ),
      home: const MainShell(),
    );
  }
}
