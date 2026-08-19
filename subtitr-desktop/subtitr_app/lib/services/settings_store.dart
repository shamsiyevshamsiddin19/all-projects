import 'package:shared_preferences/shared_preferences.dart';

/// Persists user-supplied API keys and optional model overrides.
///
/// Keys are stored locally with [SharedPreferences] (per-user, on Windows this
/// lives under the roaming AppData folder) and are injected into the Python
/// processor as environment variables at launch time. Nothing is shipped with
/// the app — every user enters their own keys.
class AppSettings {
  const AppSettings({
    this.groqApiKey = '',
    this.openaiApiKey = '',
    this.geminiApiKey = '',
    this.anthropicApiKey = '',
    this.groqWhisperModel = '',
    this.openaiModel = '',
    this.geminiModel = '',
    this.anthropicModel = '',
  });

  final String groqApiKey;
  final String openaiApiKey;
  final String geminiApiKey;
  final String anthropicApiKey;
  final String groqWhisperModel;
  final String openaiModel;
  final String geminiModel;
  final String anthropicModel;

  bool get hasAnyKey =>
      groqApiKey.trim().isNotEmpty ||
      openaiApiKey.trim().isNotEmpty ||
      geminiApiKey.trim().isNotEmpty ||
      anthropicApiKey.trim().isNotEmpty;

  /// Provider labels that are currently configured (non-empty key).
  List<String> get configuredProviders => [
        if (groqApiKey.trim().isNotEmpty) 'Groq',
        if (openaiApiKey.trim().isNotEmpty) 'OpenAI',
        if (geminiApiKey.trim().isNotEmpty) 'Gemini',
        if (anthropicApiKey.trim().isNotEmpty) 'Claude',
      ];

  /// Maps the saved settings to the environment variables the Python
  /// processor reads.
  ///
  /// The app is the single source of truth for provider config. Every managed
  /// variable is emitted explicitly — an empty string when the user left it
  /// blank — so that any ambient/inherited value on the machine (e.g. a global
  /// `ANTHROPIC_MODEL` or a proxy base URL set by another tool like Claude
  /// Code) is overridden and cannot leak into the processor. The Python side
  /// treats an empty model value as "use the built-in default".
  Map<String, String> toEnvironment() {
    String t(String v) => v.trim();
    return <String, String>{
      // API keys — empty disables that provider (won't inherit a system key).
      'GROQ_API_KEY': t(groqApiKey),
      'OPENAI_API_KEY': t(openaiApiKey),
      'GEMINI_API_KEY': t(geminiApiKey),
      'ANTHROPIC_API_KEY': t(anthropicApiKey),
      // Model overrides — empty falls back to the processor's default model.
      'GROQ_WHISPER_MODEL': t(groqWhisperModel),
      'OPENAI_MODEL': t(openaiModel),
      'GEMINI_MODEL': t(geminiModel),
      'ANTHROPIC_MODEL': t(anthropicModel),
      // Pin to official endpoints so a user's key is never routed through an
      // inherited proxy base URL.
      'ANTHROPIC_BASE_URL': 'https://api.anthropic.com',
      'OPENAI_BASE_URL': 'https://api.openai.com/v1',
    };
  }

  AppSettings copyWith({
    String? groqApiKey,
    String? openaiApiKey,
    String? geminiApiKey,
    String? anthropicApiKey,
    String? groqWhisperModel,
    String? openaiModel,
    String? geminiModel,
    String? anthropicModel,
  }) {
    return AppSettings(
      groqApiKey: groqApiKey ?? this.groqApiKey,
      openaiApiKey: openaiApiKey ?? this.openaiApiKey,
      geminiApiKey: geminiApiKey ?? this.geminiApiKey,
      anthropicApiKey: anthropicApiKey ?? this.anthropicApiKey,
      groqWhisperModel: groqWhisperModel ?? this.groqWhisperModel,
      openaiModel: openaiModel ?? this.openaiModel,
      geminiModel: geminiModel ?? this.geminiModel,
      anthropicModel: anthropicModel ?? this.anthropicModel,
    );
  }
}

/// Subtitle appearance preferences (passed to the processor as run args, not
/// environment variables).
class AppearanceSettings {
  const AppearanceSettings({
    this.fontScale = 1.0,
    this.position = 'bottom',
    this.subColor = '#FFE680',
  });

  final double fontScale; // 0.85 kichik, 1.0 o'rta, 1.2 katta
  final String position; // 'bottom' | 'top'
  final String subColor; // tarjima qatori rangi (hex)

  AppearanceSettings copyWith({double? fontScale, String? position, String? subColor}) {
    return AppearanceSettings(
      fontScale: fontScale ?? this.fontScale,
      position: position ?? this.position,
      subColor: subColor ?? this.subColor,
    );
  }
}

class SettingsStore {
  static const _kGroq = 'groq_api_key';
  static const _kOpenai = 'openai_api_key';
  static const _kGemini = 'gemini_api_key';
  static const _kAnthropic = 'anthropic_api_key';
  static const _kGroqModel = 'groq_whisper_model';
  static const _kOpenaiModel = 'openai_model';
  static const _kGeminiModel = 'gemini_model';
  static const _kAnthropicModel = 'anthropic_model';

  Future<AppSettings> load() async {
    final prefs = await SharedPreferences.getInstance();
    return AppSettings(
      groqApiKey: prefs.getString(_kGroq) ?? '',
      openaiApiKey: prefs.getString(_kOpenai) ?? '',
      geminiApiKey: prefs.getString(_kGemini) ?? '',
      anthropicApiKey: prefs.getString(_kAnthropic) ?? '',
      groqWhisperModel: prefs.getString(_kGroqModel) ?? '',
      openaiModel: prefs.getString(_kOpenaiModel) ?? '',
      geminiModel: prefs.getString(_kGeminiModel) ?? '',
      anthropicModel: prefs.getString(_kAnthropicModel) ?? '',
    );
  }

  Future<void> save(AppSettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kGroq, settings.groqApiKey.trim());
    await prefs.setString(_kOpenai, settings.openaiApiKey.trim());
    await prefs.setString(_kGemini, settings.geminiApiKey.trim());
    await prefs.setString(_kAnthropic, settings.anthropicApiKey.trim());
    await prefs.setString(_kGroqModel, settings.groqWhisperModel.trim());
    await prefs.setString(_kOpenaiModel, settings.openaiModel.trim());
    await prefs.setString(_kGeminiModel, settings.geminiModel.trim());
    await prefs.setString(_kAnthropicModel, settings.anthropicModel.trim());
  }

  Future<Map<String, String>> loadJobPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'mode': prefs.getString('job_mode') ?? 'dual_vocab',
      'source': prefs.getString('job_source') ?? 'auto',
      'target': prefs.getString('job_target') ?? 'uz',
    };
  }

  Future<void> saveJobPrefs({required String mode, required String source, required String target}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('job_mode', mode);
    await prefs.setString('job_source', source);
    await prefs.setString('job_target', target);
  }

  /// Returns true at most once per [minInterval] (default: 1 day). Used to
  /// throttle the yt-dlp self-update so it runs on the first launch of the day
  /// but not on every app start.
  Future<bool> shouldUpdateYtDlp({Duration minInterval = const Duration(days: 1)}) async {
    final prefs = await SharedPreferences.getInstance();
    final last = prefs.getInt('ytdlp_last_update_ms') ?? 0;
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - last < minInterval.inMilliseconds) return false;
    await prefs.setInt('ytdlp_last_update_ms', now);
    return true;
  }

  Future<AppearanceSettings> loadAppearance() async {
    final prefs = await SharedPreferences.getInstance();
    return AppearanceSettings(
      fontScale: prefs.getDouble('sub_font_scale') ?? 1.0,
      position: prefs.getString('sub_position') ?? 'bottom',
      subColor: prefs.getString('sub_color') ?? '#FFE680',
    );
  }

  Future<void> saveAppearance(AppearanceSettings a) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('sub_font_scale', a.fontScale);
    await prefs.setString('sub_position', a.position);
    await prefs.setString('sub_color', a.subColor);
  }
}
