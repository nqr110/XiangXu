import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../controllers/realtime_controller.dart';
import '../models/app_settings.dart';
import '../models/realtime_segment.dart';
import '../services/settings_service.dart';

enum RealtimeSessionState { idle, connecting, running, stopping }

class RealtimeState {
  const RealtimeState({
    this.sessionState = RealtimeSessionState.idle,
    this.segments = const [],
    this.lastError,
  });

  final RealtimeSessionState sessionState;
  final List<RealtimeSegment> segments;
  final String? lastError;

  RealtimeState copyWith({
    RealtimeSessionState? sessionState,
    List<RealtimeSegment>? segments,
    String? lastError,
  }) =>
      RealtimeState(
        sessionState: sessionState ?? this.sessionState,
        segments: segments ?? this.segments,
        lastError: lastError ?? this.lastError,
      );
}

final sharedPreferencesProvider = FutureProvider<SharedPreferences>((ref) async {
  return SharedPreferences.getInstance();
});

final settingsServiceProvider = Provider<SettingsService?>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  return prefs.when(
    data: (p) => SettingsService(p),
    loading: () => null,
    error: (err, stack) => null,
  );
});

final appSettingsProvider =
    StateNotifierProvider<AppSettingsNotifier, AsyncValue<AppSettings>>((ref) {
  final service = ref.watch(settingsServiceProvider);
  return AppSettingsNotifier(service);
});

class AppSettingsNotifier extends StateNotifier<AsyncValue<AppSettings>> {
  AppSettingsNotifier(this._service) : super(const AsyncValue.loading()) {
    _load();
  }

  final SettingsService? _service;

  Future<void> _load() async {
    final service = _service;
    if (service == null) {
      state = const AsyncValue.data(AppSettings());
      return;
    }
    try {
      final s = await service.loadSettings();
      state = AsyncValue.data(s);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> update(AppSettings settings) async {
    state = AsyncValue.data(settings);
    await _service?.saveSettings(settings);
  }

  void patch(AppSettings Function(AppSettings) fn) {
    state.whenData((s) {
      final next = fn(s);
      state = AsyncValue.data(next);
      final svc = _service;
      if (svc != null) {
        svc.saveSettings(next).catchError((Object e, StackTrace st) {
          // 持久化失败不向上抛，避免未捕获异常导致崩溃
        });
      }
    });
  }
}

final realtimeStateProvider =
    StateNotifierProvider<RealtimeStateNotifier, RealtimeState>((ref) {
  return RealtimeStateNotifier();
});

class RealtimeStateNotifier extends StateNotifier<RealtimeState> {
  RealtimeStateNotifier() : super(const RealtimeState());

  void setSessionState(RealtimeSessionState s) {
    state = state.copyWith(sessionState: s, lastError: s == RealtimeSessionState.idle ? null : state.lastError);
  }

  void addSegment(RealtimeSegment seg) {
    state = state.copyWith(
      segments: [...state.segments, seg],
    );
  }

  void setSegments(List<RealtimeSegment> list) {
    state = state.copyWith(segments: list);
  }

  void setLastError(String? err) {
    state = state.copyWith(lastError: err);
  }

  void clearSegments() {
    state = state.copyWith(segments: []);
  }
}

final debugLogProvider =
    StateNotifierProvider<DebugLogNotifier, List<String>>((ref) {
  return DebugLogNotifier();
});

final realtimeControllerProvider = Provider<RealtimeController>((ref) {
  return RealtimeController(ref: ref);
});

final overlayWindowIdProvider = StateProvider<int?>((ref) => null);

class DebugLogNotifier extends StateNotifier<List<String>> {
  DebugLogNotifier() : super([]);

  void add(String line) {
    state = [...state, line];
    if (state.length > 2000) {
      state = state.sublist(state.length - 1500);
    }
  }

  void clear() {
    state = [];
  }
}
