import 'dart:convert';
import 'dart:ui';

import 'package:desktop_multi_window/desktop_multi_window.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:screen_retriever/screen_retriever.dart';

import '../providers/app_providers.dart';

Future<void> createOverlayWindow(WidgetRef ref) async {
  final settings = ref.read(appSettingsProvider).valueOrNull;
  if (settings == null || !settings.subtitle.enabled) return;
  if (ref.read(overlayWindowIdProvider) != null) return;

  final subtitle = settings.subtitle;
  final args = {'subtitleSettings': subtitle.toJson()};

  final window = await DesktopMultiWindow.createWindow(jsonEncode(args));
  final windowId = window.windowId;

  double left = subtitle.positionX ?? 0;
  double top = subtitle.positionY ?? 0;
  if (subtitle.positionX == null || subtitle.positionY == null) {
    try {
      final primary = await ScreenRetriever.instance.getPrimaryDisplay();
      final w = primary.size.width;
      final h = primary.size.height;
      left = subtitle.positionX ?? (w * 0.7);
      top = subtitle.positionY ?? (h * 0.17);
    } catch (_) {
      left = 800;
      top = 100;
    }
  }

  final rect = Rect.fromLTWH(left, top, subtitle.width, subtitle.height);
  await window.setFrame(rect);
  await window.setTitle('字幕');
  await window.show();

  ref.read(overlayWindowIdProvider.notifier).state = windowId;
}

Future<void> closeOverlayWindow(WidgetRef ref) async {
  final id = ref.read(overlayWindowIdProvider);
  if (id == null) return;
  try {
    final controller = WindowController.fromWindowId(id);
    await controller.close();
  } catch (_) {}
  ref.read(overlayWindowIdProvider.notifier).state = null;
}

Future<void> sendSubtitleUpdate(WidgetRef ref, String transcription, String translation) async {
  final id = ref.read(overlayWindowIdProvider);
  if (id == null) return;
  try {
    await DesktopMultiWindow.invokeMethod(id, 'updateSubtitle', {
      'transcription': transcription,
      'translation': translation,
    });
  } catch (_) {}
}

void sendSubtitleSettingsToOverlay(WidgetRef ref) {
  final settings = ref.read(appSettingsProvider).valueOrNull;
  final id = ref.read(overlayWindowIdProvider);
  if (settings == null || !settings.subtitle.enabled || id == null) return;
  DesktopMultiWindow.invokeMethod(id, 'updateSettings', settings.subtitle.toJson()).catchError((Object e, StackTrace st) {});
}

void setupMainWindowMethodHandler(WidgetRef ref) {
  DesktopMultiWindow.setMethodHandler((call, fromWindowId) async {
    if (call.method == 'positionChanged' && call.arguments is Map) {
      final map = Map<String, dynamic>.from(call.arguments as Map);
      final x = (map['x'] as num?)?.toDouble();
      final y = (map['y'] as num?)?.toDouble();
      if (x != null && y != null) {
        ref.read(appSettingsProvider.notifier).patch((s) => s.copyWith(
              subtitle: s.subtitle.copyWith(positionX: x, positionY: y),
            ));
      }
    }
    return null;
  });
}
