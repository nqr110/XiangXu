import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_settings.dart';

const String _keySettings = 'app_settings';

class SettingsService {
  SettingsService(this._prefs);

  final SharedPreferences _prefs;

  Future<AppSettings> loadSettings() async {
    final raw = _prefs.getString(_keySettings);
    if (raw == null || raw.isEmpty) return const AppSettings();
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return AppSettings.fromJson(map);
    } catch (_) {
      return const AppSettings();
    }
  }

  Future<void> saveSettings(AppSettings settings) async {
    await _prefs.setString(_keySettings, jsonEncode(settings.toJson()));
  }
}
