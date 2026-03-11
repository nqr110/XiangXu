import 'dart:async';

/// 系统音频采集服务。当前为占位实现，后续可接入 desktop_audio_capture 或 Win32 环回采集。
class SystemAudioCaptureService {
  StreamSubscription<List<int>>? _sub;
  final _controller = StreamController<List<int>>.broadcast();

  /// 目标采样率，与阿里云 run-task 的 sample_rate 一致（如 16000）。
  int get sampleRate => 16000;

  /// 是否正在采集
  bool get isCapturing => _sub != null;

  /// PCM 流（单声道 16bit，已重采样到 [sampleRate] 则可由调用方保证）。
  Stream<List<int>> get audioStream => _controller.stream;

  /// 开始采集。deviceId 为 null 或 'system_mix' 时使用默认系统混音。
  Future<void> start({String? deviceId}) async {
    if (_sub != null) return;
    // 占位：不产生真实音频；实际实现时在此启动 desktop_audio_capture 或 Win32 环回，
    // 将数据重采样到 sampleRate、单声道后通过 _controller.add 推送。
    _sub = const Stream<List<int>>.empty().listen((_) {});
  }

  /// 停止采集
  Future<void> stop() async {
    await _sub?.cancel();
    _sub = null;
  }

  void dispose() {
    _controller.close();
  }
}
