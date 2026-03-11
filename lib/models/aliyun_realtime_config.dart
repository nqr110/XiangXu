class AliyunRealtimeConfig {
  const AliyunRealtimeConfig({
    this.model = 'gummy-realtime-v1',
    this.sampleRate = 16000,
    this.format = 'pcm',
    this.enableRecognition = true,
    this.enableTranslation = true,
    this.sourceLanguage = 'auto',
    this.translationTargetLanguages = const ['zh'],
  });

  final String model;
  final int sampleRate;
  final String format;
  final bool enableRecognition;
  final bool enableTranslation;
  final String sourceLanguage;
  final List<String> translationTargetLanguages;

  Map<String, dynamic> toRunTaskPayload() => {
        'task_group': 'audio',
        'task': 'asr',
        'function': 'recognition',
        'model': model,
        'input': <String, dynamic>{},
        'parameters': {
          'sample_rate': sampleRate,
          'format': format,
          'transcription_enabled': enableRecognition,
          'translation_enabled': enableTranslation,
          if (sourceLanguage.isNotEmpty) 'source_language': sourceLanguage,
          if (enableTranslation && translationTargetLanguages.isNotEmpty)
            'translation_target_languages': translationTargetLanguages,
        },
      };
}
