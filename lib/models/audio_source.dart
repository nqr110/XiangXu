class AudioSource {
  const AudioSource({
    required this.id,
    required this.displayName,
    this.isDefault = false,
  });

  final String id;
  final String displayName;
  final bool isDefault;

  static const String systemMixId = 'system_mix';

  static AudioSource get systemMix => const AudioSource(
        id: systemMixId,
        displayName: '全部系统声音（推荐）',
        isDefault: true,
      );
}
