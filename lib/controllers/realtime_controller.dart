import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/aliyun_realtime_config.dart';
import '../models/app_settings.dart';
import '../models/realtime_segment.dart';
import '../providers/app_providers.dart';
import '../services/aliyun_realtime_service.dart';
import '../services/system_audio_capture_service.dart';

class RealtimeController {
  RealtimeController({
    required this.ref,
  }) : _audio = SystemAudioCaptureService();

  final Ref ref;
  final SystemAudioCaptureService _audio;

  AliyunRealtimeService? _aliyun;
  StreamSubscription<RealtimeSegment>? _segmentSub;
  StreamSubscription<List<int>>? _audioSub;
  Timer? _audioTimer;
  final List<int> _audioBuffer = [];

  static const int chunkMs = 100;
  static const int sampleRate = 16000;
  static const int bytesPerSample = 2;
  static const int chunkBytes = (sampleRate * chunkMs ~/ 1000) * bytesPerSample;

  Future<void> start() async {
    final settings = ref.read(appSettingsProvider).valueOrNull;
    if (settings == null || settings.apiKey.isEmpty) return;

    ref.read(realtimeStateProvider.notifier).clearSegments();
    ref.read(debugLogProvider.notifier).add('[Realtime] 正在连接…');
    ref.read(realtimeStateProvider.notifier).setSessionState(RealtimeSessionState.connecting);

    final config = _configFromSettings(settings);
    _aliyun = AliyunRealtimeService(
      apiKey: settings.apiKey,
      onDebugLog: (line) => ref.read(debugLogProvider.notifier).add(line),
    );

    try {
      await _aliyun!.startSession(config);
    } catch (e) {
      ref.read(realtimeStateProvider.notifier).setSessionState(RealtimeSessionState.idle);
      ref.read(realtimeStateProvider.notifier).setLastError(e.toString());
      ref.read(debugLogProvider.notifier).add('[Realtime] 连接失败: $e');
      return;
    }

    ref.read(realtimeStateProvider.notifier).setSessionState(RealtimeSessionState.running);
    ref.read(debugLogProvider.notifier).add('[Realtime] 已连接，开始采集音频');

    _segmentSub = _aliyun!.segmentStream.listen((seg) {
      ref.read(realtimeStateProvider.notifier).addSegment(seg);
    });

    await _audio.start(deviceId: settings.audioSourceId);

    _audioSub = _audio.audioStream.listen((chunk) {
      _audioBuffer.addAll(chunk);
    });

    _audioTimer = Timer.periodic(const Duration(milliseconds: chunkMs), (_) {
      while (_audioBuffer.length >= chunkBytes) {
        final send = _audioBuffer.sublist(0, chunkBytes);
        _audioBuffer.removeRange(0, chunkBytes);
        _aliyun?.sendAudioChunk(send);
      }
    });
  }

  AliyunRealtimeConfig _configFromSettings(AppSettings s) {
    final mode = s.recognitionMode;
    return AliyunRealtimeConfig(
      enableRecognition: mode == RecognitionMode.recognitionOnly || mode == RecognitionMode.both,
      enableTranslation: mode == RecognitionMode.translationOnly || mode == RecognitionMode.both,
      sourceLanguage: s.sourceLanguage,
      translationTargetLanguages: [s.targetLanguage],
    );
  }

  Future<void> stop() async {
    ref.read(realtimeStateProvider.notifier).setSessionState(RealtimeSessionState.stopping);
    _audioTimer?.cancel();
    _audioTimer = null;
    await _audioSub?.cancel();
    _audioSub = null;
    _audioBuffer.clear();
    await _segmentSub?.cancel();
    _segmentSub = null;
    await _aliyun?.finishSession();
    _aliyun?.dispose();
    _aliyun = null;
    await _audio.stop();
    ref.read(realtimeStateProvider.notifier).setSessionState(RealtimeSessionState.idle);
    ref.read(debugLogProvider.notifier).add('[Realtime] 已停止');
  }
}
