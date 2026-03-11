class RealtimeSegment {
  const RealtimeSegment({
    required this.sentenceId,
    required this.beginTime,
    required this.endTime,
    this.transcriptionText = '',
    this.translationTexts = const {},
    this.sentenceEnd = false,
  });

  final int sentenceId;
  final int beginTime;
  final int endTime;
  final String transcriptionText;
  final Map<String, String> translationTexts;
  final bool sentenceEnd;

  bool get isFinal => sentenceEnd;

  String get primaryTranslation {
    if (translationTexts.isEmpty) return '';
    return translationTexts.values.first;
  }
}
