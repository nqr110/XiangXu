import 'dart:ui';

enum RecognitionMode { recognitionOnly, translationOnly, both }

enum SubtitleAlignmentMode { left, center, right, split }

class SubtitleWindowSettings {
  const SubtitleWindowSettings({
    this.enabled = false,
    this.alwaysOnTop = false,
    this.clickThrough = false,
    this.cornerRadius = 12.0,
    this.backgroundColor = const Color(0xFF1E1E1E),
    this.backgroundOpacity = 0.85,
    this.textColor = const Color(0xFFFFFFFF),
    this.textOpacity = 1.0,
    this.fontFamily = 'Microsoft YaHei',
    this.alignmentMode = SubtitleAlignmentMode.center,
    this.width = 600.0,
    this.height = 180.0,
    this.positionX,
    this.positionY,
  });

  final bool enabled;
  final bool alwaysOnTop;
  final bool clickThrough;
  final double cornerRadius;
  final Color backgroundColor;
  final double backgroundOpacity;
  final Color textColor;
  final double textOpacity;
  final String fontFamily;
  final SubtitleAlignmentMode alignmentMode;
  final double width;
  final double height;
  final double? positionX;
  final double? positionY;

  SubtitleWindowSettings copyWith({
    bool? enabled,
    bool? alwaysOnTop,
    bool? clickThrough,
    double? cornerRadius,
    Color? backgroundColor,
    double? backgroundOpacity,
    Color? textColor,
    double? textOpacity,
    String? fontFamily,
    SubtitleAlignmentMode? alignmentMode,
    double? width,
    double? height,
    double? positionX,
    double? positionY,
  }) {
    return SubtitleWindowSettings(
      enabled: enabled ?? this.enabled,
      alwaysOnTop: alwaysOnTop ?? this.alwaysOnTop,
      clickThrough: clickThrough ?? this.clickThrough,
      cornerRadius: cornerRadius ?? this.cornerRadius,
      backgroundColor: backgroundColor ?? this.backgroundColor,
      backgroundOpacity: backgroundOpacity ?? this.backgroundOpacity,
      textColor: textColor ?? this.textColor,
      textOpacity: textOpacity ?? this.textOpacity,
      fontFamily: fontFamily ?? this.fontFamily,
      alignmentMode: alignmentMode ?? this.alignmentMode,
      width: width ?? this.width,
      height: height ?? this.height,
      positionX: positionX ?? this.positionX,
      positionY: positionY ?? this.positionY,
    );
  }

  Map<String, dynamic> toJson() => {
        'enabled': enabled,
        'alwaysOnTop': alwaysOnTop,
        'clickThrough': clickThrough,
        'cornerRadius': cornerRadius,
        'backgroundColor': backgroundColor.toARGB32(),
        'backgroundOpacity': backgroundOpacity,
        'textColor': textColor.toARGB32(),
        'textOpacity': textOpacity,
        'fontFamily': fontFamily,
        'alignmentMode': alignmentMode.index,
        'width': width,
        'height': height,
        'positionX': positionX,
        'positionY': positionY,
      };

  static SubtitleWindowSettings fromJson(Map<String, dynamic> json) {
    return SubtitleWindowSettings(
      enabled: json['enabled'] as bool? ?? false,
      alwaysOnTop: json['alwaysOnTop'] as bool? ?? false,
      clickThrough: json['clickThrough'] as bool? ?? false,
      cornerRadius: (json['cornerRadius'] as num?)?.toDouble() ?? 12.0,
      backgroundColor: Color(json['backgroundColor'] as int? ?? 0xFF1E1E1E),
      backgroundOpacity: (json['backgroundOpacity'] as num?)?.toDouble() ?? 0.85,
      textColor: Color(json['textColor'] as int? ?? 0xFFFFFFFF),
      textOpacity: (json['textOpacity'] as num?)?.toDouble() ?? 1.0,
      fontFamily: json['fontFamily'] as String? ?? 'Microsoft YaHei',
      alignmentMode: SubtitleAlignmentMode.values[
          (json['alignmentMode'] as int?)?.clamp(0, SubtitleAlignmentMode.values.length - 1) ?? 1],
      width: (json['width'] as num?)?.toDouble() ?? 600.0,
      height: (json['height'] as num?)?.toDouble() ?? 180.0,
      positionX: (json['positionX'] as num?)?.toDouble(),
      positionY: (json['positionY'] as num?)?.toDouble(),
    );
  }
}

class AppSettings {
  const AppSettings({
    this.apiKey = '',
    this.recognitionMode = RecognitionMode.both,
    this.sourceLanguage = 'auto',
    this.targetLanguage = 'zh',
    this.audioSourceId,
    this.subtitle = const SubtitleWindowSettings(),
  });

  final String apiKey;
  final RecognitionMode recognitionMode;
  final String sourceLanguage;
  final String targetLanguage;
  final String? audioSourceId;
  final SubtitleWindowSettings subtitle;

  AppSettings copyWith({
    String? apiKey,
    RecognitionMode? recognitionMode,
    String? sourceLanguage,
    String? targetLanguage,
    String? audioSourceId,
    SubtitleWindowSettings? subtitle,
  }) {
    return AppSettings(
      apiKey: apiKey ?? this.apiKey,
      recognitionMode: recognitionMode ?? this.recognitionMode,
      sourceLanguage: sourceLanguage ?? this.sourceLanguage,
      targetLanguage: targetLanguage ?? this.targetLanguage,
      audioSourceId: audioSourceId ?? this.audioSourceId,
      subtitle: subtitle ?? this.subtitle,
    );
  }

  Map<String, dynamic> toJson() => {
        'apiKey': apiKey,
        'recognitionMode': recognitionMode.index,
        'sourceLanguage': sourceLanguage,
        'targetLanguage': targetLanguage,
        'audioSourceId': audioSourceId,
        'subtitle': subtitle.toJson(),
      };

  static AppSettings fromJson(Map<String, dynamic> json) {
    return AppSettings(
      apiKey: json['apiKey'] as String? ?? '',
      recognitionMode: RecognitionMode.values[
          (json['recognitionMode'] as int?)?.clamp(0, RecognitionMode.values.length - 1) ?? 2],
      sourceLanguage: json['sourceLanguage'] as String? ?? 'auto',
      targetLanguage: json['targetLanguage'] as String? ?? 'zh',
      audioSourceId: json['audioSourceId'] as String?,
      subtitle: json['subtitle'] != null
          ? SubtitleWindowSettings.fromJson(
              Map<String, dynamic>.from(json['subtitle'] as Map))
          : const SubtitleWindowSettings(),
    );
  }
}
