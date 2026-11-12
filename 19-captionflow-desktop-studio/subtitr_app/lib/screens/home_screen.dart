import 'dart:async';
import 'dart:io';
import 'dart:ui' show AppExitResponse;

import 'package:file_picker/file_picker.dart';
import 'package:desktop_drop/desktop_drop.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
// ignore: depend_on_referenced_packages
import 'package:package_info_plus/package_info_plus.dart';

import '../services/desktop_processor_service.dart';
import '../services/settings_store.dart';
import '../widgets/processing_panel.dart';
import '../widgets/settings_panel.dart';
import '../widgets/video_selection_panel.dart';
import '../widgets/in_app_video_player.dart';
import '../widgets/home_job_dialogs.dart';
import '../widgets/home_screen_chrome.dart';
import '../widgets/history_panel.dart';
import '../widgets/subtitle_player.dart' show playerAvailable;
import 'api_keys_screen.dart';
import 'translation_editor_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.autoScan = true});

  final bool autoScan;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  String? _appVersion;
  final DesktopProcessorService _service = DesktopProcessorService();
  final SettingsStore _settingsStore = SettingsStore();
  AppSettings _settings = const AppSettings();
  AppearanceSettings _appearance = const AppearanceSettings();
  String _batchInfo = ''; // "Video 2/5" — navbat holati
  List<JobPreset> _presets = const [];
  List<BatchResult> _batchResults = const [];
  final List<_AppNotification> _notifications = [];
  int _unreadNotificationCount = 0;
  bool _isDragging = false;
  bool _showHistory = false;
  List<HistoryEntry> _historyItems = const [];

  List<DesktopVideo> _videos = const [];
  DesktopVideo? _selectedVideo;
  ProcessorResult? _result;
  String? _externalVideoPath;
  String? _externalSubtitlePath;
  String? _externalSubtitleVideoPath;
  double _subtitleOffset = 0;
  String _kinoDir = '';
  String _outDir = '';
  String _mode = 'dual_vocab';
  String _sourceLang = 'auto';
  String _targetLang = 'uz';
  String _voice = 'uz-UZ-SardorNeural';
  double _ducking = 0.18;
  String _status = 'Tayyor';
  double _progress = 0;
  bool _loading = true;
  bool _running = false;
  String? _currentDir;
  String? _activePlayerVideo;
  String? _activePlayerSubtitle;
  String? _activePlayerTitle;
  double _videoDuration = 0.0;
  DateTime? _startTime;
  DateTime? _lastProgressUpdate;
  Timer? _timer;

  static const _modes = [
    ModeChoice(
      value: 'dual_vocab',
      icon: Icons.view_sidebar_rounded,
      title: 'Tarjima + lug\'at',
      description: 'Pastda original va tarjima, chapda so\'zlar',
    ),
    ModeChoice(
      value: 'original_vocab',
      icon: Icons.subtitles_rounded,
      title: 'Original + lug\'at',
      description: 'Pastda faqat original, chapda so\'zlar',
    ),
    ModeChoice(
      value: 'dual',
      icon: Icons.layers_rounded,
      title: 'Ikki qator subtitr',
      description: 'Original va tarjima pastda',
    ),
    ModeChoice(
      value: 'original',
      icon: Icons.closed_caption_rounded,
      title: 'Original subtitr',
      description: 'Faqat original subtitr kuydiriladi',
    ),
    ModeChoice(
      value: 'translated',
      icon: Icons.translate_rounded,
      title: 'Faqat tarjima',
      description: 'Videoda faqat tarjima subtitri ko\'rinadi',
    ),
    ModeChoice(
      value: 'softsub',
      icon: Icons.closed_caption_rounded,
      title: '2 ta alohida trek (CC)',
      description: "Pleyerda tilni almashtirish (Original / Tarjima)",
    ),
    ModeChoice(
      value: 'softsub_dual',
      icon: Icons.subtitles_rounded,
      title: 'Ikki qatorli subtitr',
      description: "Asl matn va tarjima birgalikda",
    ),
    ModeChoice(
      value: 'softsub_translated',
      icon: Icons.translate_rounded,
      title: 'Faqat tarjima',
      description: "Kadrda faqat tarjima tili",
    ),
    ModeChoice(
      value: 'softsub_original',
      icon: Icons.language_rounded,
      title: 'Faqat asl matn',
      description: "Faqat original til (Ingliz/Rus...)",
    ),
    ModeChoice(
      value: 'dubbing',
      icon: Icons.record_voice_over_rounded,
      title: "AI Dublyaj (Ko'p tilli)",
      description: "O'zbekcha AI ovoz, asl musiqa saqlanadi (Multi-audio)",
    ),
    ModeChoice(
      value: 'reading',
      icon: Icons.auto_stories_rounded,
      title: 'O\'qish uchun matn',
      description: 'PDF (3 xil maket), TXT va Yordamchi sayti uchun MD',
    ),
    ModeChoice(
      value: 'srt',
      icon: Icons.description_rounded,
      title: 'SRT fayl',
      description: 'Original va tarjima SRT fayllari',
    ),
    ModeChoice(
      value: 'transcript',
      icon: Icons.article_rounded,
      title: 'Matn TXT/DOCX',
      description: 'Matn va tarjimasi hujjatga',
    ),
    ModeChoice(
      value: 'vocabulary',
      icon: Icons.menu_book_rounded,
      title: 'Lug\'at TXT/DOCX',
      description: 'So\'zlar va tarjimasi hujjatga',
    ),
    ModeChoice(
      value: 'all',
      icon: Icons.all_inclusive_rounded,
      title: 'Hammasi',
      description: 'Video, SRT, matn va lug\'at',
    ),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadSettings();
    _loadAppVersion();
    if (widget.autoScan) {
      // autoScan also gates background startup work (skipped under widget tests,
      // which launch with autoScan: false to avoid spawning the processor).
      _maybeUpdateYtDlp();
      _scanVideos();
    } else {
      _loading = false;
      _status = 'Tayyor';
    }
  }

  /// Keeps the bundled yt-dlp fresh so downloads keep working as sites change.
  /// Throttled to once per day; runs quietly in the background.
  Future<void> _maybeUpdateYtDlp() async {
    try {
      if (await _settingsStore.shouldUpdateYtDlp()) {
        await _service.updateYtDlp();
      }
    } catch (_) {}
  }

  Future<void> _loadSettings() async {
    final settings = await _settingsStore.load();
    final appearance = await _settingsStore.loadAppearance();
    final job = await _settingsStore.loadJobPrefs();
    final lastResult = await _settingsStore.loadLastResult();
    final presets = await _settingsStore.loadPresets();
    _service.processEnvironment = settings.toEnvironment();
    if (mounted) {
      setState(() {
        _settings = settings;
        _appearance = appearance;
        _mode = job['mode'] ?? _mode;
        _sourceLang = job['source'] ?? _sourceLang;
        _targetLang = job['target'] ?? _targetLang;
        _voice = job['voice'] ?? _voice;
        _ducking = double.tryParse(job['ducking'] ?? '') ?? _ducking;
        _presets = presets;
        // Ilova qayta ochilganda oldingi videoning natijasi bo'sh ekrandan
        // ko'ra ko'proq foydali — foydalanuvchi so'nggi yakunlangan ishni
        // darhol ko'radi, qayta ishga tushirishga hojat qolmaydi.
        if (lastResult != null) {
          _result = lastResult;
          _outDir = lastResult.outDir;
        }
      });
    }
  }

  Future<void> _handleDrop(List<DropItem> files) async {
    if (_running || files.isEmpty) return;
    final paths = files.map((file) => file.path).whereType<String>().toList();

    // Agar papka tashlangan bo'lsa, uni kino papkasi sifatida ochish
    final droppedDir = paths
        .where((p) => Directory(p).existsSync())
        .firstOrNull;
    if (droppedDir != null) {
      await _scanVideos(path: droppedDir);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Papka ochildi: ${File(droppedDir).uri.pathSegments.where((s) => s.isNotEmpty).lastOrNull ?? droppedDir}',
            ),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      return;
    }

    const videoExtensions = {'mp4', 'mkv', 'avi', 'mov', 'webm', 'm4v'};
    const subtitleExtensions = {'srt', 'vtt', 'ass', 'ssa'};
    final video = paths
        .where(
          (path) =>
              videoExtensions.contains(path.split('.').last.toLowerCase()),
        )
        .firstOrNull;
    final subtitle = paths
        .where(
          (path) =>
              subtitleExtensions.contains(path.split('.').last.toLowerCase()),
        )
        .firstOrNull;
    if (video == null && subtitle == null) {
      _showError(
        'Faqat video, papka yoki SRT/VTT/ASS subtitr faylini tashlang',
      );
      return;
    }
    setState(() {
      if (video != null) {
        _selectedVideo = null;
        _externalVideoPath = video;
        _dropManualSubtitleForOtherVideo(video);
        _result = null;
        _status = 'Tashlab qo\'yilgan video tanlandi';
      }
      if (subtitle != null) {
        _externalSubtitlePath = subtitle;
        _externalSubtitleVideoPath = video ?? _selectedPath;
        _status = video == null
            ? 'Tashlab qo\'yilgan subtitr tanlandi'
            : _status;
      }
    });
    if (video != null) await _updateDuration();
  }

  Future<void> _savePreset() async {
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Presetni saqlash'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Nomi, masalan: YouTube 1080p',
          ),
          onSubmitted: (value) => Navigator.pop(context, value.trim()),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Bekor qilish'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Saqlash'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (name == null || name.isEmpty) return;
    final preset = JobPreset(
      name: name,
      mode: _mode,
      source: _sourceLang,
      target: _targetLang,
      voice: _voice,
      ducking: _ducking,
      appearance: _appearance,
      subtitleOffset: _subtitleOffset,
    );
    await _settingsStore.savePreset(preset);
    if (!mounted) return;
    setState(
      () => _presets = [
        ..._presets.where(
          (item) => item.name.toLowerCase() != name.toLowerCase(),
        ),
        preset,
      ],
    );
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Preset saqlandi'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _deletePreset(JobPreset preset) async {
    await _settingsStore.deletePreset(preset.name);
    if (!mounted) return;
    setState(
      () => _presets = _presets
          .where((item) => item.name != preset.name)
          .toList(),
    );
  }

  void _applyPreset(JobPreset preset) {
    setState(() {
      _mode = preset.mode;
      _sourceLang = preset.source;
      _targetLang = preset.target;
      _voice = preset.voice;
      _ducking = preset.ducking;
      _appearance = preset.appearance;
      _subtitleOffset = preset.subtitleOffset;
    });
    _saveJobPrefs();
    _settingsStore.saveAppearance(preset.appearance);
  }

  void _saveJobPrefs() {
    _settingsStore.saveJobPrefs(
      mode: _mode,
      source: _sourceLang,
      target: _targetLang,
      voice: _voice,
      ducking: _ducking,
    );
  }

  void _updateAppearance(AppearanceSettings a) {
    setState(() => _appearance = a);
    _settingsStore.saveAppearance(a);
  }

  Future<void> _openSettings() async {
    final updated = await Navigator.of(context).push<AppSettings>(
      MaterialPageRoute(builder: (_) => ApiKeysScreen(initial: _settings)),
    );
    if (updated == null || !mounted) return;
    _service.processEnvironment = updated.toEnvironment();
    setState(() => _settings = updated);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('API kalitlar saqlandi'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _updateDuration() async {
    final path = _externalVideoPath ?? _selectedVideo?.path;
    // URL uchun davomiylikni o'lchamaymiz (video hali yuklab olinmagan).
    if (path == null || path.isEmpty || path.startsWith('http')) {
      if (mounted) setState(() => _videoDuration = 0.0);
      return;
    }
    final d = await _service.probeDuration(path);
    if (mounted) {
      setState(() => _videoDuration = d);
    }
  }

  Future<void> _startFromUrl(String url) async {
    setState(() {
      _selectedVideo = null;
      _externalVideoPath = url;
      _dropManualSubtitleForOtherVideo(url);
      _result = null;
      _videoDuration = 0.0;
      _status = 'Havola tanlandi';
    });
    await _startProcessing();
  }

  /// Faqat videoni yuklab oladi (subtitrsiz) va papkani ochadi.
  Future<void> _loadAppVersion() async {
    try {
      final info = await PackageInfo.fromPlatform();
      if (!mounted) return;
      final build = info.buildNumber.isEmpty ? '' : '+${info.buildNumber}';
      setState(() => _appVersion = '${info.version}$build');
    } catch (_) {}
  }

  /// Yagona ish yurituvchi: taymer, holat, bekor qilish va xatolarni
  /// barcha jarayonlar (_downloadOnly, _startProcessing, _reviewAndRender)
  /// uchun markazlashtirilgan holda boshqaradi.
  Future<void> _runJob(
    String initialStatus,
    Future<void> Function() action,
  ) async {
    setState(() {
      _running = true;
      _activePlayerVideo = null;
      _result = null;
      _progress = 0;
      _status = initialStatus;
      _startTime = DateTime.now();
      _lastProgressUpdate = DateTime.now();
    });
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
    try {
      await action();
    } on ProcessorCancelled {
      if (mounted) {
        setState(() {
          _status = 'Bekor qilindi';
          _progress = 0;
        });
      }
    } catch (error) {
      _showError(error.toString());
    } finally {
      _timer?.cancel();
      if (mounted) {
        setState(() {
          _running = false;
          _startTime = null;
        });
      }
    }
  }

  Future<void> _downloadOnly(String url) async {
    await _runJob('Video yuklab olinmoqda', () async {
      final res = await _service.downloadUrl(
        url: url,
        onProgress: _applyProgress,
        quality: _appearance.quality,
      );
      if (!mounted) return;
      final dir = res['dir'] as String? ?? '';
      final name = res['name'] as String? ?? 'video';
      final downloadedPath = res['path'] as String? ?? '';
      setState(() {
        _status = 'Yuklandi: $name';
        _progress = 1;
        if (downloadedPath.isNotEmpty && File(downloadedPath).existsSync()) {
          _externalVideoPath = downloadedPath;
          _selectedVideo = null;
        }
      });
      _recordNotification('Video muvaffaqiyatli yuklandi: $name');
      await _updateDuration();
      if (dir.isNotEmpty) await _openPath(dir);
    });
  }

  Future<void> _scanVideos({String? path}) async {
    setState(() {
      _loading = true;
    });
    try {
      final targetPath = path ?? _currentDir;
      final scan = await _service.scan(path: targetPath);
      if (!mounted) return;
      setState(() {
        _currentDir = targetPath;
        _videos = scan.videos;
        _kinoDir = scan.kinoDir;
        _outDir = scan.outDir;

        if (_selectedVideo != null &&
            !_videos.any((v) => v.path == _selectedVideo!.path)) {
          _selectedVideo = null;
        }
        if (_selectedVideo == null) {
          final firstFile = _videos.where((v) => !v.isDir).firstOrNull;
          _selectedVideo = firstFile;
        }

        _externalVideoPath = null;
        _dropManualSubtitleForOtherVideo(_selectedVideo?.path ?? '');
        _status = _videos.isEmpty
            ? 'Kinolar papkasiga video tashlang'
            : 'Tayyor';
      });
      _updateDuration();
    } catch (error) {
      _showError(error.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _pickExternalVideo() async {
    final picked = await FilePicker.pickFiles(type: FileType.video);
    final path = picked?.files.single.path;
    if (path == null || !mounted) {
      return;
    }
    setState(() {
      _selectedVideo = null;
      _externalVideoPath = path;
      _dropManualSubtitleForOtherVideo(path);
      _result = null;
      _status = 'Tashqi video tanlandi';
    });
    _updateDuration();
  }

  Future<void> _pickExternalSubtitle() async {
    final picked = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['srt', 'vtt', 'ass', 'ssa'],
    );
    final path = picked?.files.single.path;
    if (path == null || !mounted) return;
    setState(() {
      _externalSubtitlePath = path;
      _externalSubtitleVideoPath = _selectedPath.isEmpty ? null : _selectedPath;
      _result = null;
      _status = 'Tashqi subtitr tanlandi';
    });
  }

  Future<void> _installDependencies() async {
    setState(() {
      _running = true;
      _result = null;
      _status = 'Paketlar o\'rnatilmoqda';
      _progress = 0.08;
    });
    try {
      await _service.installDependencies(onProgress: _applyProgress);
      if (!mounted) return;
      setState(() {
        _status = 'Paketlar tayyor';
        _progress = 1;
      });
    } catch (error) {
      _showError(error.toString());
    } finally {
      if (mounted) {
        setState(() => _running = false);
      }
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    super.dispose();
  }

  /// Ilova yopilayotganda joriy jarayonni (va u ishga tushirgan ffmpeg/yt-dlp
  /// "bolalarini") to'xtatadi — aks holda ular fonda ishlab qolaverardi.
  /// `didRequestAppExit` — oynaning X tugmasi orqali yopilishi (desktop uchun
  /// Flutterning rasmiy yo'li); `detached` holati qo'shimcha ehtiyot chorasi.
  @override
  Future<AppExitResponse> didRequestAppExit() async {
    await _service.cancel();
    return AppExitResponse.exit;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.detached) {
      _service.cancel();
    }
  }

  Future<void> _startProcessing() async {
    final path = _externalVideoPath ?? _selectedVideo?.path;
    if (path == null || path.isEmpty) {
      _showError('Avval video tanlang');
      return;
    }
    if (!_settings.hasAnyKey) {
      final proceed = await _confirmNoKeys();
      if (proceed != true) {
        if (proceed == false) _openSettings();
        return;
      }
    }
    await _runJob('Boshlanmoqda', () async {
      final result = await _service.process(
        videoPath: path,
        mode: _mode,
        sourceLang: _sourceLang,
        targetLang: _targetLang,
        onProgress: _applyProgress,
        fontScale: _appearance.fontScale,
        position: _appearance.position,
        subColor: _appearance.subColor,
        origStyle: _appearance.origStyle,
        quality: _appearance.quality,
        upscale: _appearance.upscale,
        subtitlePath: _subtitleFor(path),
        subtitleOffset: _subtitleOffsetFor(path),
        voice: _voice,
        ducking: _ducking,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _status = 'Yakunlandi';
        _progress = 1;
      });
      _settingsStore.saveLastResult(result);
      _recordNotification('Muvaffaqiyatli yakunlandi: $_selectedName');
    });
  }

  /// Two-phase flow (#1): transcribe+translate, let the user review/edit the
  /// translation, then render. Slower to start but gives full control.
  Future<void> _reviewAndRender() async {
    final path = _externalVideoPath ?? _selectedVideo?.path;
    if (path == null || path.isEmpty) {
      _showError('Avval video tanlang');
      return;
    }
    if (!_settings.hasAnyKey) {
      final proceed = await _confirmNoKeys();
      if (proceed != true) {
        if (proceed == false) _openSettings();
        return;
      }
    }

    PreparedSession? session;
    await _runJob('Matn tayyorlanmoqda', () async {
      session = await _service.prepare(
        videoPath: path,
        mode: _mode,
        sourceLang: _sourceLang,
        targetLang: _targetLang,
        onProgress: _applyProgress,
        subtitlePath: _subtitleFor(path),
        subtitleOffset: _subtitleOffsetFor(path),
        voice: _voice,
        ducking: _ducking,
      );
    });
    if (session == null || !mounted) return;

    // Review/edit screen — returns edited segments, or null if cancelled.
    final edited = await Navigator.of(context).push<List<SubtitleSegment>>(
      MaterialPageRoute(
        builder: (_) => TranslationEditorScreen(
          session: session!,
          appearance: _appearance,
          service: _service,
        ),
      ),
    );
    if (edited == null || !mounted) {
      setState(() => _status = 'Tayyor');
      return;
    }

    // Phase 2 — render the edited translation.
    await _runJob('Render qilinmoqda', () async {
      final result = await _service.render(
        sessionPath: session!.sessionPath,
        segments: edited,
        onProgress: _applyProgress,
        fontScale: _appearance.fontScale,
        position: _appearance.position,
        subColor: _appearance.subColor,
        origStyle: _appearance.origStyle,
        quality: _appearance.quality,
        upscale: _appearance.upscale,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _status = 'Yakunlandi';
        _progress = 1;
      });
      _settingsStore.saveLastResult(result);
      _recordNotification(
        'Tahrirlangan subtitr bilan yakunlandi: $_selectedName',
      );
      await _service.discardDraft(session!.sessionPath);
    });
  }

  Future<void> _cancelProcessing() async {
    _batchCancelled = true;
    setState(() => _status = 'To\'xtatilmoqda...');
    await _service.cancel();
  }

  bool _batchCancelled = false;

  /// Joriy papkadagi barcha videolarni ketma-ket qayta ishlaydi (navbat).
  Future<void> _startBatch() async {
    final videos = _videos.where((v) => !v.isDir).toList();
    if (videos.isEmpty) {
      _showError('Papkada video topilmadi');
      return;
    }
    // Bitta qo'lda tanlangan subtitrni turli videolarga jimgina qo'llash
    // noto'g'ri vaqt/matn beradi. Navbatda har video o'z yonidagi sidecar
    // subtitrini oladi; qo'lda import qilingan fayl esa faqat bitta video
    // uchun ishlatiladi.
    if (_externalSubtitlePath != null) {
      _showError(
        'Tashqi subtitr bitta video uchun tanlangan. Navbatdan oldin uni olib tashlang; navbat har video yonidagi subtitrni avtomatik oladi.',
      );
      return;
    }
    if (!_settings.hasAnyKey) {
      final proceed = await _confirmNoKeys();
      if (proceed != true) {
        if (proceed == false) _openSettings();
        return;
      }
    }
    if (!mounted) return;
    final queue = await showDialog<List<DesktopVideo>>(
      context: context,
      builder: (_) => BatchQueueDialog(videos: videos),
    );
    if (queue == null || queue.isEmpty || !mounted) return;
    await _runVideoBatch(queue);
  }

  /// Runs exactly the selection/order approved in [_BatchQueueDialog]. A
  /// cancelled job stops before the next queue item and preserves completed
  /// and failed item details for the user to inspect.
  Future<void> _runVideoBatch(List<DesktopVideo> videos) async {
    _batchCancelled = false;
    _batchResults = const [];
    setState(() {
      _running = true;
      _result = null;
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
    final results = <BatchResult>[];
    try {
      for (var i = 0; i < videos.length; i++) {
        if (_batchCancelled) break;
        final v = videos[i];
        setState(() {
          _batchInfo = 'Video ${i + 1}/${videos.length}';
          _progress = 0;
          _status = '$_batchInfo: ${v.name}';
          _startTime = DateTime.now();
        });
        try {
          final result = await _service.process(
            videoPath: v.path,
            mode: _mode,
            sourceLang: _sourceLang,
            targetLang: _targetLang,
            onProgress: _applyProgress,
            fontScale: _appearance.fontScale,
            position: _appearance.position,
            subColor: _appearance.subColor,
            origStyle: _appearance.origStyle,
            quality: _appearance.quality,
            upscale: _appearance.upscale,
            subtitlePath: v.subtitlePath,
            subtitleOffset: v.subtitlePath.isNotEmpty ? _subtitleOffset : 0,
            voice: _voice,
            ducking: _ducking,
          );
          results.add(BatchResult(video: v, success: true));
          if (mounted) setState(() => _result = result);
          _settingsStore.saveLastResult(result);
        } on ProcessorCancelled {
          break;
        } catch (error) {
          results.add(
            BatchResult(video: v, success: false, detail: error.toString()),
          );
        }
      }
      if (mounted) {
        setState(() {
          _progress = _batchCancelled ? 0 : 1;
          _batchResults = List.unmodifiable(results);
          final done = results.where((item) => item.success).length;
          final failed = results.where((item) => !item.success).length;
          _status = _batchCancelled
              ? 'Bekor qilindi ($done tayyor)'
              : 'Navbat yakunlandi: $done tayyor${failed > 0 ? ", $failed xato" : ""}';
        });
        _recordNotification(_status);
      }
    } finally {
      _timer?.cancel();
      if (mounted) {
        setState(() {
          _running = false;
          _startTime = null;
          _batchInfo = '';
        });
      }
    }
  }

  /// Playlist ro'yxati avval faqat metama'lumot sifatida olinadi. Foydalanuvchi
  /// tanlagan URLlar esa mavjud batch mexanizmi kabi birma-bir ishlanadi.
  Future<void> _loadPlaylistQueue(String url) async {
    try {
      final entries = await _service.playlist(url: url, limit: 25);
      if (!mounted) return;
      final selected = await showDialog<List<PlaylistEntry>>(
        context: context,
        builder: (_) => PlaylistPickerDialog(entries: entries),
      );
      if (selected == null || selected.isEmpty || !mounted) return;
      await _startUrlBatch(selected);
    } catch (error) {
      _showError(error.toString());
    }
  }

  Future<void> _startUrlBatch(List<PlaylistEntry> entries) async {
    if (_externalSubtitlePath != null) {
      _showError(
        'Tashqi subtitr playlist navbatiga qo\'llanmaydi. Uni olib tashlab qayta urinib ko\'ring.',
      );
      return;
    }
    _batchCancelled = false;
    await _runJob('Playlist navbati boshlanmoqda', () async {
      var done = 0;
      var failed = 0;
      for (var i = 0; i < entries.length && !_batchCancelled; i++) {
        final entry = entries[i];
        if (mounted) {
          setState(() {
            _batchInfo = 'Video ${i + 1}/${entries.length}';
            _status = '$_batchInfo: ${entry.title}';
            _progress = 0;
          });
        }
        try {
          final result = await _service.process(
            videoPath: entry.url,
            mode: _mode,
            sourceLang: _sourceLang,
            targetLang: _targetLang,
            onProgress: _applyProgress,
            fontScale: _appearance.fontScale,
            position: _appearance.position,
            subColor: _appearance.subColor,
            origStyle: _appearance.origStyle,
            quality: _appearance.quality,
            upscale: _appearance.upscale,
            voice: _voice,
            ducking: _ducking,
          );
          done++;
          if (mounted) {
            setState(() => _result = result);
          }
          _settingsStore.saveLastResult(result);
        } on ProcessorCancelled {
          break;
        } catch (_) {
          failed++;
        }
      }
      if (mounted) {
        setState(() {
          _status = _batchCancelled
              ? 'Bekor qilindi ($done tayyor)'
              : 'Navbat yakunlandi: $done tayyor${failed > 0 ? ', $failed xato' : ''}';
          _progress = _batchCancelled ? 0 : 1;
        });
        _recordNotification(_status);
      }
    });
  }

  /// Returns true to continue anyway, false to open settings, null to cancel.
  Future<bool?> _confirmNoKeys() {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.key_off_rounded),
        title: const Text('API kalit kiritilmagan'),
        content: const Text(
          'Kalitsiz dastur faqat video yonidagi tayyor .srt yoki oflayn '
          'lug\'at bilan ishlaydi. Sifatli transkripsiya va tarjima uchun '
          'o\'z API kalitingizni kiriting.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(null),
            child: const Text('Bekor qilish'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Baribir davom etish'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Kalit kiritish'),
          ),
        ],
      ),
    );
  }

  void _applyProgress(ProcessorProgress progress) {
    if (!mounted) return;
    setState(() {
      _status = progress.message.isEmpty ? _status : progress.message;
      final nextProgress = progress.progress.clamp(0, 1).toDouble();
      // Xabar o'zgarishi foiz siljigani degani emas. Yakuniy PDF/DOCX
      // yozilishida aynan foizning oxirgi o'zgargan vaqtini saqlaymiz.
      if (nextProgress != _progress) _lastProgressUpdate = DateTime.now();
      _progress = nextProgress;
    });
  }

  /// Qo'lda import qilingan subtitr sidecar fayldan ustun turadi. Aks holda
  /// skaner topgan `film.srt` avtomatik ravishda aynan o'sha videoga beriladi.
  String? _subtitleFor(String videoPath) {
    final external = _externalSubtitlePath;
    if (external != null &&
        external.isNotEmpty &&
        (_externalSubtitleVideoPath == null ||
            _externalSubtitleVideoPath == videoPath)) {
      return external;
    }
    final selected = _selectedVideo;
    if (selected != null &&
        selected.path == videoPath &&
        selected.subtitlePath.isNotEmpty) {
      return selected.subtitlePath;
    }
    return null;
  }

  /// Vaqt siljishi faqat import qilingan subtitrga tegishli. Aks holda eski
  /// presetdagi offset yangi transkripsiyani ham sababsiz surib yuboradi.
  double _subtitleOffsetFor(String videoPath) =>
      _subtitleFor(videoPath) == null ? 0 : _subtitleOffset;

  /// Qo'lda tanlangan subtitr bitta video bilan bog'langan. Video almashtirilsa
  /// eski matn boshqa filmga qo'llanib ketmasligi uchun uni olib tashlaymiz.
  /// Ushbu metod faqat `setState` ichida chaqiriladi.
  void _dropManualSubtitleForOtherVideo(String videoPath) {
    if (_externalSubtitlePath == null) return;
    final owner = _externalSubtitleVideoPath;
    if (owner == null) {
      _externalSubtitleVideoPath = videoPath;
    } else if (owner != videoPath) {
      _externalSubtitlePath = null;
      _externalSubtitleVideoPath = null;
      _subtitleOffset = 0;
    }
  }

  bool _isVideoPath(String path) {
    const videoExts = {'mp4', 'mkv', 'avi', 'mov', 'webm', 'm4v', 'flv', 'ts'};
    final dot = path.lastIndexOf('.');
    if (dot == -1) return false;
    final ext = path.substring(dot + 1).toLowerCase();
    return videoExts.contains(ext);
  }

  Future<void> _openPath(String path) async {
    try {
      if (_isVideoPath(path) && playerAvailable) {
        String? sub;
        if (_result != null) {
          // Asl (original) subtitrni birinchi navbatda tanlaymiz
          final orig = _result!.outputs
              .where(
                (o) =>
                    (o.kind == 'ass' || o.kind == 'srt') &&
                    (o.name.toLowerCase().contains('original') ||
                        o.name.toLowerCase().contains('orig')),
              )
              .firstOrNull;
          sub =
              orig?.path ??
              _result!.outputs
                  .where((o) => o.kind == 'ass' || o.kind == 'srt')
                  .firstOrNull
                  ?.path;
        }
        if (sub == null || !File(sub).existsSync()) {
          final dot = path.lastIndexOf('.');
          if (dot > 0) {
            final base = path.substring(0, dot);
            final candidates = [
              '${base}_original.srt',
              '${base}_original.ass',
              '${base}_orig.srt',
              '${base}_orig_soft.ass',
              '${base}_softsub_original.ass',
              '$base.ass',
              '$base.srt',
              '$base.vtt',
            ];
            for (final c in candidates) {
              if (File(c).existsSync()) {
                sub = c;
                break;
              }
            }
          }
        }

        setState(() {
          _activePlayerVideo = path;
          _activePlayerSubtitle = sub;
          _activePlayerTitle = File(path).uri.pathSegments.last;
        });
        return;
      }
      await _service.openPath(path);
    } catch (error) {
      _showError(error.toString());
    }
  }

  /// Test uchun: xato oqimini tashqaridan ishga tushirish.
  @visibleForTesting
  void showErrorForTest(String message) => _showError(message);

  void _showError(String message) {
    if (!mounted) return;
    setState(() {
      _status = message;
      _running = false;
      _recordNotification(message, isError: true);
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, maxLines: 3, overflow: TextOverflow.ellipsis),
        behavior: SnackBarBehavior.floating,
        // ffmpeg va provayder xatolari uzun bo'ladi va uch qatordan
        // keyin kesiladi — aynan kerakli qismi shu yerda yo'qolardi.
        action: SnackBarAction(
          label: 'Batafsil',
          onPressed: () => _showErrorDetail(message),
        ),
        duration: const Duration(seconds: 8),
      ),
    );
  }

  /// So'nggi jarayonlar bitta joyda ko'rinadi; bir xil progress xabari esa
  /// ro'yxatni to'ldirib yubormaydi.
  void _recordNotification(String message, {bool isError = false}) {
    final text = message.trim();
    if (text.isEmpty) return;
    final first = _notifications.firstOrNull;
    if (first != null && first.message == text && first.isError == isError) {
      return;
    }
    _notifications.insert(
      0,
      _AppNotification(message: text, isError: isError, time: DateTime.now()),
    );
    if (_notifications.length > 20) _notifications.removeLast();
    _unreadNotificationCount = (_unreadNotificationCount + 1)
        .clamp(0, 99)
        .toInt();
  }

  Future<void> _showNotifications() async {
    setState(() => _unreadNotificationCount = 0);
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Bildirishnomalar'),
        content: SizedBox(
          width: 420,
          child: _notifications.isEmpty
              ? const Text('Hali bildirishnoma yo\'q.')
              : ListView.separated(
                  shrinkWrap: true,
                  itemCount: _notifications.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (_, index) {
                    final item = _notifications[index];
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(
                        item.isError
                            ? Icons.error_outline_rounded
                            : Icons.info_outline_rounded,
                        color: item.isError
                            ? Theme.of(context).colorScheme.error
                            : Theme.of(context).colorScheme.primary,
                      ),
                      title: Text(item.message),
                      subtitle: Text(
                        '${item.time.hour.toString().padLeft(2, '0')}:${item.time.minute.toString().padLeft(2, '0')}',
                      ),
                    );
                  },
                ),
        ),
        actions: [
          if (_notifications.isNotEmpty)
            TextButton(
              onPressed: () {
                setState(_notifications.clear);
                Navigator.of(context).pop();
              },
              child: const Text('Tozalash'),
            ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Yopish'),
          ),
        ],
      ),
    );
  }

  void _toggleHistory() {
    setState(() {
      _showHistory = !_showHistory;
      if (_showHistory) {
        _activePlayerVideo = null;
        _loadHistory();
      }
    });
  }

  void _loadHistory() {
    final targetDir = _outDir.isNotEmpty
        ? _outDir
        : '${Platform.environment['HOME']}/Videos/Subtitr natijalar';
    final dir = Directory(targetDir);

    final items = <HistoryEntry>[];
    if (dir.existsSync()) {
      try {
        final entries = dir.listSync();
        for (final entry in entries) {
          if (entry is Directory) {
            final files = entry.listSync();
            final videoFile = files
                .whereType<File>()
                .where((f) {
                  final l = f.path.toLowerCase();
                  return l.endsWith('.mp4') ||
                      l.endsWith('.mkv') ||
                      l.endsWith('.webm') ||
                      l.endsWith('.mov');
                })
                .firstOrNull;
            final subtitleFile = files
                .whereType<File>()
                .where((f) {
                  final l = f.path.toLowerCase();
                  return l.endsWith('.srt') || l.endsWith('.ass');
                })
                .firstOrNull;
            final rawName = entry.path.split(Platform.pathSeparator).last;
            final cleanName = rawName
                .replaceAll(RegExp(r'__\w+$'), '')
                .replaceAll('_', ' ')
                .trim();
            items.add(HistoryEntry(
              name: cleanName.isNotEmpty ? cleanName : rawName,
              directoryPath: entry.path,
              videoPath: videoFile?.path,
              subtitlePath: subtitleFile?.path,
              modified: entry.statSync().modified,
            ));
          } else if (entry is File) {
            final l = entry.path.toLowerCase();
            if (l.endsWith('.mp4') || l.endsWith('.mkv') || l.endsWith('.webm')) {
              final rawName = entry.path.split(Platform.pathSeparator).last;
              final cleanName = rawName
                  .replaceAll(RegExp(r'\.[^.]+$'), '')
                  .replaceAll(RegExp(r'__\w+$'), '')
                  .replaceAll('_', ' ')
                  .trim();
              items.add(HistoryEntry(
                name: cleanName.isNotEmpty ? cleanName : rawName,
                directoryPath: entry.parent.path,
                videoPath: entry.path,
                subtitlePath: null,
                modified: entry.statSync().modified,
              ));
            }
          }
        }
      } catch (_) {}
    }

    items.sort((a, b) => b.modified.compareTo(a.modified));
    setState(() {
      _historyItems = items;
    });
  }

  /// Shows the full error with a copy button.
  ///
  /// The snackbar truncates at three lines, and an ffmpeg or provider
  /// failure puts the useful part at the end. Without this the user could
  /// only see the beginning of a message they then could not report.
  Future<void> _showErrorDetail(String message) async {
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.error_outline_rounded),
        title: const Text('Xato tafsiloti'),
        content: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560, maxHeight: 420),
          child: SingleChildScrollView(
            child: SelectableText(
              message,
              style: const TextStyle(fontSize: 13, height: 1.4),
            ),
          ),
        ),
        actions: [
          TextButton.icon(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: message));
              if (!context.mounted) return;
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Nusxa olindi'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            icon: const Icon(Icons.copy_rounded, size: 18),
            label: const Text('Nusxa olish'),
          ),
          TextButton.icon(
            onPressed: () async {
              Navigator.of(context).pop();
              try {
                final dir = await _service.logDir();
                if (dir.isNotEmpty) await _openPath(dir);
              } catch (_) {}
            },
            icon: const Icon(Icons.folder_open_rounded, size: 18),
            // To'liq iz (traceback) faqat logda bo'ladi.
            label: const Text('Loglarni ochish'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Yopish'),
          ),
        ],
      ),
    );
  }

  String get _selectedPath => _externalVideoPath ?? _selectedVideo?.path ?? '';
  String get _selectedName {
    final p = _externalVideoPath;
    if (p != null) {
      if (p.startsWith('http')) return 'Havola (yuklab olinadi)';
      return File(p).uri.pathSegments.last;
    }
    return _selectedVideo?.name ?? 'Video tanlanmagan';
  }

  int get _estimatedSeconds {
    double factor = 0.35;
    if (_mode == 'all') factor = 0.5;
    if (_mode == 'srt' || _mode == 'transcript' || _mode == 'reading') {
      factor = 0.15;
    }
    return (_videoDuration * factor).round();
  }

  /// Tarjima qiladigan rejimlar — Python tarafdagi `pipeline._prepare_data`
  /// ichidagi `needs_translation` to'plami bilan AYNAN bir xil bo'lishi kerak.
  /// Ilgari bu yerda `const needsTr = true` turardi va "Original" rejimlarida
  /// ham tarjima tokeni va'da qilinardi — aslida hech qanday tarjima
  /// so'rovi ketmasdi.
  static const _translatingModes = {
    'dual',
    'dual_vocab',
    'translated',
    'softsub',
    'softsub_dual',
    'softsub_translated',
    'srt',
    'transcript',
    'reading',
    'all',
  };

  /// Lug'at tuzadigan rejimlar — `pipeline._prepare_data` dagi `VOCAB_MODES`.
  static const _vocabModes = {
    'vocabulary',
    'original_vocab',
    'dual_vocab',
    'all',
  };

  /// Rough token estimate so the user knows about how much they'll spend.
  String get _estimateText {
    if (_videoDuration <= 0) return '';
    final segs = (_videoDuration / 3.5).round();
    var tokens = 0;
    if (_translatingModes.contains(_mode)) tokens += segs * 45;
    if (_vocabModes.contains(_mode)) tokens += segs * 25;
    if (tokens <= 0) return '~$segs subtitr';
    final k = (tokens / 1000).round();
    return '~$segs subtitr · ~$k ming token';
  }

  @override
  Widget build(BuildContext context) {
    return DropTarget(
      onDragDone: (detail) {
        setState(() => _isDragging = false);
        _handleDrop(detail.files);
      },
      onDragEntered: (_) => setState(() => _isDragging = true),
      onDragExited: (_) => setState(() => _isDragging = false),
      child: Stack(
        children: [
          CallbackShortcuts(
            bindings: <ShortcutActivator, VoidCallback>{
              const SingleActivator(
                LogicalKeyboardKey.keyO,
                control: true,
              ): () {
                if (!_running) _pickExternalVideo();
              },
              const SingleActivator(LogicalKeyboardKey.keyO, meta: true): () {
                if (!_running) _pickExternalVideo();
              },
              const SingleActivator(
                LogicalKeyboardKey.enter,
                control: true,
              ): () {
                if (!_running) _startProcessing();
              },
              const SingleActivator(LogicalKeyboardKey.enter, meta: true): () {
                if (!_running) _startProcessing();
              },
              const SingleActivator(LogicalKeyboardKey.escape): () {
                if (_running) _cancelProcessing();
              },
            },
            child: Focus(
              autofocus: true,
              child: Scaffold(
                appBar: HomeScreenAppBar(
                  appVersion: _appVersion,
                  hasApiKey: _settings.hasAnyKey,
                  configuredProviders: _settings.configuredProviders,
                  isRunning: _running,
                  unreadNotificationCount: _unreadNotificationCount,
                  canOpenOutput: _outDir.isNotEmpty,
                  isHistoryOpen: _showHistory,
                  onShowHistory: _toggleHistory,
                  onOpenApiKeys: _openSettings,
                  onInstallDependencies: _installDependencies,
                  onShowNotifications: _showNotifications,
                  onOpenOutput: () => _openPath(_outDir),
                ),
                body: SafeArea(
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      final wide = constraints.maxWidth >= 1040;

                      final videoPanel = VideoSelectionPanel(
                        kinoDir: _kinoDir,
                        currentDir: _currentDir,
                        videos: _videos,
                        selectedVideo: _selectedVideo,
                        externalVideoPath: _externalVideoPath,
                        externalSubtitlePath: _externalSubtitlePath,
                        subtitleOffset: _subtitleOffset,
                        isRunning: _running,
                        isLoading: _loading,
                        onScan: () => _scanVideos(path: _currentDir),
                        onPickExternal: _pickExternalVideo,
                        onPickSubtitle: _pickExternalSubtitle,
                        onClearSubtitle: () => setState(() {
                          _externalSubtitlePath = null;
                          _externalSubtitleVideoPath = null;
                          _subtitleOffset = 0;
                        }),
                        onOffsetChanged: (value) =>
                            setState(() => _subtitleOffset = value),
                        onSelectVideo: (v) {
                          if (v.isDir) {
                            _scanVideos(path: v.path);
                          } else {
                            setState(() {
                              _selectedVideo = v;
                              _externalVideoPath = null;
                              _dropManualSubtitleForOtherVideo(v.path);
                              _result = null;
                            });
                            _updateDuration();
                          }
                        },
                        onNavigateBack: () {
                          if (_currentDir != null && _kinoDir != _currentDir) {
                            final parent = File(_currentDir!).parent.path;
                            _scanVideos(path: parent);
                          }
                        },
                        onClearExternal: () {
                          setState(() {
                            _externalVideoPath = null;
                            _selectedVideo = _videos
                                .where((v) => !v.isDir)
                                .firstOrNull;
                            _dropManualSubtitleForOtherVideo(
                              _selectedVideo?.path ?? '',
                            );
                          });
                          _updateDuration();
                        },
                        onUrlSubmit: _startFromUrl,
                        onDownloadOnly: _downloadOnly,
                        onPlaylistSubmit: _loadPlaylistQueue,
                        onPreviewVideo: _openPath,
                      );

                      final settingsPanel = SettingsPanel(
                        modes: _modes,
                        mode: _mode,
                        sourceLang: _sourceLang,
                        targetLang: _targetLang,
                        appearance: _appearance,
                        voice: _voice,
                        ducking: _ducking,
                        isRunning: _running,
                        onModeChanged: (v) {
                          setState(() => _mode = v);
                          _saveJobPrefs();
                        },
                        onSourceLangChanged: (v) {
                          setState(() => _sourceLang = v);
                          _saveJobPrefs();
                        },
                        onTargetLangChanged: (v) {
                          setState(() => _targetLang = v);
                          _saveJobPrefs();
                        },
                        onAppearanceChanged: _updateAppearance,
                        onVoiceChanged: (v) {
                          setState(() => _voice = v);
                          _saveJobPrefs();
                        },
                        onDuckingChanged: (v) {
                          setState(() => _ducking = v);
                          _saveJobPrefs();
                        },
                        presets: _presets,
                        onSavePreset: _savePreset,
                        onApplyPreset: _applyPreset,
                        onDeletePreset: _deletePreset,
                        onPickSubtitle: _pickExternalSubtitle,
                        externalSubtitlePath: _externalSubtitlePath,
                        onClearSubtitle: () => setState(() {
                          _externalSubtitlePath = null;
                          _externalSubtitleVideoPath = null;
                          _subtitleOffset = 0;
                        }),
                      );

                      final processor = ProcessingPanel(
                        selectedName: _selectedName,
                        selectedPath: _selectedPath,
                        outDir: _result?.outDir.isNotEmpty == true
                            ? _result!.outDir
                            : _outDir,
                        isRunning: _running,
                        progress: _progress,
                        status: _status,
                        result: _result,
                        estimatedSeconds: _estimatedSeconds,
                        estimateText: _estimateText,
                        startTime: _startTime,
                        lastProgressUpdate: _lastProgressUpdate,
                        onStart: _startProcessing,
                        onReview: _reviewAndRender,
                        onCancel: _cancelProcessing,
                        onStartBatch: _startBatch,
                        videoCount: _videos.where((v) => !v.isDir).length,
                        onOpenPath: _openPath,
                      );
                      final batchCard = _batchResults.isEmpty
                          ? null
                          : BatchResultsCard(
                              results: _batchResults,
                              onDetail: _showErrorDetail,
                            );

                      final historyPanel = HistoryPanel(
                        items: _historyItems,
                        onClose: () => setState(() => _showHistory = false),
                        onPlay: (p) {
                          setState(() => _showHistory = false);
                          _openPath(p);
                        },
                        onOpenFolder: (p) => _service.openPath(p),
                        onOpenOutputFolder: () => _openPath(
                          _outDir.isNotEmpty
                              ? _outDir
                              : '${Platform.environment['HOME']}/Videos/Subtitr natijalar',
                        ),
                        onRefresh: _loadHistory,
                      );

                      final rightContent = _activePlayerVideo != null
                          ? EmbeddedVideoPlayer(
                              videoPath: _activePlayerVideo!,
                              subtitlePath: _activePlayerSubtitle,
                              title: _activePlayerTitle,
                              onClose: () {
                                setState(() {
                                  _activePlayerVideo = null;
                                  _activePlayerSubtitle = null;
                                  _activePlayerTitle = null;
                                });
                              },
                              onOpenExternal: (p) => _service.openPath(p),
                            )
                          : _showHistory
                              ? historyPanel
                              : processor;

                      final wideRightColumn = Column(
                        children: [
                          Expanded(child: rightContent),
                          if (batchCard case final Widget card) card,
                        ],
                      );

                      if (wide) {
                        final leftColumn = Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            videoPanel,
                            const SizedBox(height: 24),
                            Expanded(child: settingsPanel),
                          ],
                        );
                        return Padding(
                          padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              SizedBox(width: 440, child: leftColumn),
                              const SizedBox(width: 24),
                              Container(
                                width: 1,
                                color: const Color(0xFF333333),
                              ),
                              const SizedBox(width: 24),
                              Expanded(child: wideRightColumn),
                            ],
                          ),
                        );
                      }

                      return ListView(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                        children: [
                          if (_showHistory) ...[
                            SizedBox(height: 500, child: historyPanel),
                            const SizedBox(height: 16),
                          ],
                          if (_activePlayerVideo != null) ...[
                            SizedBox(
                              height: 440,
                              child: EmbeddedVideoPlayer(
                                videoPath: _activePlayerVideo!,
                                subtitlePath: _activePlayerSubtitle,
                                title: _activePlayerTitle,
                                onClose: () {
                                  setState(() {
                                    _activePlayerVideo = null;
                                    _activePlayerSubtitle = null;
                                    _activePlayerTitle = null;
                                  });
                                },
                                onOpenExternal: (p) => _service.openPath(p),
                              ),
                            ),
                            const SizedBox(height: 16),
                          ],
                          videoPanel,
                          const SizedBox(height: 16),
                          settingsPanel,
                          const SizedBox(height: 16),
                          processor,
                          if (batchCard case final Widget card) ...[
                            const SizedBox(height: 16),
                            card,
                          ],
                        ],
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
          if (_isDragging) const HomeDropOverlay(),
        ],
      ),
    );
  }
}

class _AppNotification {
  const _AppNotification({
    required this.message,
    required this.isError,
    required this.time,
  });

  final String message;
  final bool isError;
  final DateTime time;
}
