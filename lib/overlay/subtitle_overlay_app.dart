import 'package:desktop_multi_window/desktop_multi_window.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../models/app_settings.dart';

class SubtitleOverlayApp extends StatefulWidget {
  const SubtitleOverlayApp({
    super.key,
    required this.windowId,
    required this.args,
  });

  final int windowId;
  final Map<String, dynamic> args;

  @override
  State<SubtitleOverlayApp> createState() => _SubtitleOverlayAppState();
}

class _SubtitleOverlayAppState extends State<SubtitleOverlayApp> {
  String _transcription = '';
  String _translation = '';
  SubtitleWindowSettings? _settings;

  @override
  void initState() {
    super.initState();
    _parseArgs();
    DesktopMultiWindow.setMethodHandler(_onMethodCall);
  }

  void _parseArgs() {
    final args = widget.args;
    if (args['subtitleSettings'] != null) {
      try {
        _settings = SubtitleWindowSettings.fromJson(
          Map<String, dynamic>.from(args['subtitleSettings'] as Map),
        );
      } catch (_) {}
    }
    _settings ??= const SubtitleWindowSettings();
  }

  Future<dynamic> _onMethodCall(MethodCall call, int fromWindowId) async {
    if (call.method == 'updateSubtitle') {
      final map = call.arguments as Map<dynamic, dynamic>?;
      if (map != null) {
        if (mounted) {
          setState(() {
            _transcription = map['transcription']?.toString() ?? '';
            _translation = map['translation']?.toString() ?? '';
          });
        }
      }
    }
    if (call.method == 'updateSettings') {
      final raw = call.arguments;
      if (raw is! Map) return null;
      try {
        final parsed = SubtitleWindowSettings.fromJson(
          Map<String, dynamic>.from(raw as Map),
        );
        if (mounted) {
          setState(() => _settings = parsed);
        }
      } catch (_) {}
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final s = _settings ?? const SubtitleWindowSettings();
    final bgColor = s.backgroundColor.withValues(alpha: s.backgroundOpacity);
    final textColor = s.textColor.withValues(alpha: s.textOpacity);

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: '字幕',
      theme: ThemeData.dark(),
      home: Scaffold(
        backgroundColor: Colors.transparent,
        body: ClipRRect(
          borderRadius: BorderRadius.circular(s.cornerRadius),
          child: Container(
            width: double.infinity,
            height: double.infinity,
            color: bgColor,
            alignment: _alignmentFromMode(s.alignmentMode),
            padding: const EdgeInsets.all(12),
            child: _buildContent(s, textColor),
          ),
        ),
      ),
    );
  }

  Alignment _alignmentFromMode(SubtitleAlignmentMode mode) {
    switch (mode) {
      case SubtitleAlignmentMode.left:
        return Alignment.centerLeft;
      case SubtitleAlignmentMode.right:
        return Alignment.centerRight;
      case SubtitleAlignmentMode.center:
        return Alignment.center;
      case SubtitleAlignmentMode.split:
        return Alignment.center;
    }
  }

  Widget _buildContent(SubtitleWindowSettings s, Color textColor) {
    final textStyle = TextStyle(
      color: textColor,
      fontFamily: s.fontFamily,
      fontSize: 16,
    );
    if (s.alignmentMode == SubtitleAlignmentMode.split) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(_transcription, style: textStyle),
            ),
          ),
          Expanded(
            child: Align(
              alignment: Alignment.centerRight,
              child: Text(_translation, style: textStyle),
            ),
          ),
        ],
      );
    }
    final combined = _transcription.isEmpty && _translation.isEmpty
        ? ''
        : _translation.isNotEmpty
            ? '$_transcription\n$_translation'
            : _transcription;
    return Text(combined, style: textStyle);
  }
}
