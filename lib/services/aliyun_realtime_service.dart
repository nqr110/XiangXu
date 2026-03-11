import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/aliyun_realtime_config.dart';
import '../models/realtime_segment.dart';

const String _wsUrl = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference';

class AliyunRealtimeService {
  AliyunRealtimeService({
    required String apiKey,
    void Function(String)? onDebugLog,
  })  : _apiKey = apiKey,
        _onDebugLog = onDebugLog ?? ((String line) {});

  final String _apiKey;
  final void Function(String) _onDebugLog;

  WebSocketChannel? _channel;
  StreamSubscription? _streamSubscription;
  String? _taskId;
  final _segmentController = StreamController<RealtimeSegment>.broadcast();
  Stream<RealtimeSegment> get segmentStream => _segmentController.stream;

  bool _taskStarted = false;
  bool _closed = false;

  static String _generateTaskId() {
    final r = Random();
    final hex = List.generate(32, (_) => r.nextInt(16).toRadixString(16)).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-${hex.substring(12, 16)}-${hex.substring(16, 20)}-${hex.substring(20)}';
  }

  Future<void> startSession(AliyunRealtimeConfig config) async {
    if (_channel != null) {
      await stopSession();
    }
    _closed = false;
    _taskStarted = false;
    _taskId = _generateTaskId();

    final headers = {
      'Authorization': 'Bearer $_apiKey',
      'User-Agent': 'XiangXuFlutter/1.0',
    };

    _onDebugLog('WebSocket connecting to $_wsUrl');
    _channel = IOWebSocketChannel.connect(
      Uri.parse(_wsUrl),
      headers: headers,
    );

    final runTaskPayload = {
      'header': {
        'action': 'run-task',
        'task_id': _taskId,
        'streaming': 'duplex',
      },
      'payload': config.toRunTaskPayload(),
    };
    _channel!.sink.add(utf8.encode(jsonEncode(runTaskPayload)));
    _onDebugLog('Sent run-task, task_id=$_taskId');

    await _waitForTaskStarted();
  }

  Future<void> _waitForTaskStarted() async {
    final completer = Completer<void>();
    _streamSubscription = _channel!.stream.listen(
      (data) {
        if (_closed) return;
        final text = data is List<int> ? utf8.decode(data) : data is String ? data : null;
        if (text != null) _handleMessage(text, completer);
      },
      onError: (e, st) {
        _onDebugLog('WebSocket error: $e');
        if (!completer.isCompleted) completer.completeError(e, st);
      },
      onDone: () {
        if (!completer.isCompleted) completer.completeError(Exception('WebSocket closed before task-started'));
      },
      cancelOnError: false,
    );
    await completer.future;
  }

  void _handleMessage(String text, Completer<void> taskStartedCompleter) {
    try {
      final map = jsonDecode(text) as Map<String, dynamic>;
      final header = map['header'] as Map<String, dynamic>?;
      final event = header?['event'] as String?;
      if (event == 'task-started') {
        _taskStarted = true;
        _onDebugLog('Received task-started');
        if (!taskStartedCompleter.isCompleted) taskStartedCompleter.complete();
        return;
      }
      if (event == 'task-finished') {
        _onDebugLog('Received task-finished');
        return;
      }
      if (event == 'task-failed') {
        final code = header?['error_code'] ?? '';
        final msg = header?['error_message'] ?? '';
        _onDebugLog('task-failed: $code $msg');
        if (!taskStartedCompleter.isCompleted) {
          taskStartedCompleter.completeError('$code: $msg');
        }
        return;
      }
      if (event != 'result-generated') return;
      {
        final payload = map['payload'] as Map<String, dynamic>?;
        final output = payload?['output'] as Map<String, dynamic>?;
        if (output == null) return;
        final transcription = output['transcription'] as Map<String, dynamic>?;
        final translations = output['translations'] as List<dynamic>?;
        final sentenceEnd = transcription?['sentence_end'] as bool? ?? false;
        final sentenceId = (transcription?['sentence_id'] as num?)?.toInt() ?? 0;
        final beginTime = (transcription?['begin_time'] as num?)?.toInt() ?? 0;
        final endTime = (transcription?['end_time'] as num?)?.toInt() ?? 0;
        final transText = transcription?['text'] as String? ?? '';
        final Map<String, String> transMap = {};
        if (translations != null) {
          for (final t in translations) {
            if (t is Map<String, dynamic>) {
              final lang = t['lang'] as String? ?? 'zh';
              final text = t['text'] as String? ?? '';
              transMap[lang] = text;
            }
          }
        }
        _segmentController.add(RealtimeSegment(
          sentenceId: sentenceId,
          beginTime: beginTime,
          endTime: endTime,
          transcriptionText: transText,
          translationTexts: transMap,
          sentenceEnd: sentenceEnd,
        ));
      }
    } on Object catch (e) {
      _onDebugLog('Parse message error: $e');
    }
  }

  void sendAudioChunk(List<int> pcmBytes) {
    if (!_taskStarted || _channel == null || _closed) return;
    _channel!.sink.add(pcmBytes);
  }

  Future<void> finishSession() async {
    if (_channel == null || _taskId == null) return;
    final finishPayload = {
      'header': {
        'action': 'finish-task',
        'task_id': _taskId,
        'streaming': 'duplex',
      },
      'payload': {'input': <String, dynamic>{}},
    };
    _channel!.sink.add(utf8.encode(jsonEncode(finishPayload)));
    _onDebugLog('Sent finish-task');
    await Future<void>.delayed(const Duration(milliseconds: 500));
    _closed = true;
    await _channel!.sink.close();
    _channel = null;
    _taskId = null;
    _taskStarted = false;
  }

  Future<void> stopSession() async {
    _closed = true;
    await _streamSubscription?.cancel();
    _streamSubscription = null;
    if (_channel != null) {
      await _channel!.sink.close();
      _channel = null;
    }
    _taskId = null;
    _taskStarted = false;
  }

  void dispose() {
    _segmentController.close();
  }
}
