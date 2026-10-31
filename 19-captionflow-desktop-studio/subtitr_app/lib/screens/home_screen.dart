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
import '../widgets/subtitle_player.dart' show playerAvailable;
import 'api_keys_screen.dart';
import 'translation_editor_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.autoScan = true});

  final bool autoScan;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _PlaylistPickerDialog extends StatefulWidget {
  const _PlaylistPickerDialog({required this.entries});
  final List<PlaylistEntry> entries;

  @override
  State<_PlaylistPickerDialog> createState() => _PlaylistPickerDialogState();
}

class _PlaylistPickerDialogState extends State<_PlaylistPickerDialog> {
  late final Set<String> _selected = widget.entries
      .map((e) => e.url)
      .take(25)
      .toSet();

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Playlistdan videolarni tanlang'),
    content: SizedBox(
      width: 560,
      child: ListView.builder(
        shrinkWrap: true,
        itemCount: widget.entries.length,
        itemBuilder: (_, index) {
          final entry = widget.entries[index];
          return CheckboxListTile(
            value: _selected.contains(entry.url),
            title: Text(
              entry.title,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: entry.duration.isEmpty
                ? null
                : Text('${entry.duration} soniya'),
            onChanged: (checked) => setState(() {
              if (checked == true && _selected.length < 25) {
                _selected.add(entry.url);
              }
              if (checked != true) {
                _selected.remove(entry.url);
              }
            }),
          );
        },
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Bekor qilish'),
      ),
      FilledButton(
        onPressed: _selected.isEmpty
            ? null
            : () => Navigator.pop(
                context,
                widget.entries.where((e) => _selected.contains(e.url)).toList(),
              ),
        child: Text('${_selected.length} ta navbatga qo\'shish'),
      ),
    ],
  );
}

class _HomeScreenState extends State<HomeScreen> with WidgetsBindingObserver {
  String? _appVersion;
  final DesktopProcessorService _service = DesktopProcessorService();
  final SettingsStore _settingsStore = SettingsStore();
  AppSettings _settings = const AppSettings();
  AppearanceSettings _appearance = const AppearanceSettings();
  String _batchInfo = ''; // "Video 2/5" — navbat holati
  List<JobPreset> _presets = const [];
  List<_BatchResult> _batchResults = const [];

  List<DesktopVideo> _videos = const [];
  DesktopVideo? _selectedVideo;
  ProcessorResult? _result;
  String? _externalVideoPath;
  String? _externalSubtitlePath;
  double _subtitleOffset = 0;
  String _kinoDir = '';
  String _outDir = '';
  String _mode = 'dual_vocab';
  String _sourceLang = 'auto';
  String _targetLang = 'uz';
  String _status = 'Tayyor';
  double _progress = 0;
  bool _loading = true;
  bool _running = false;
  String? _currentDir;
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
    const videoExtensions = {'mp4', 'mkv', 'avi', 'mov', 'webm', 'm4v'};
    const subtitleExtensions = {'srt', 'vtt', 'ass', 'ssa'};
    final paths = files.map((file) => file.path).whereType<String>().toList();
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
      _showError('Faqat video yoki SRT/VTT/ASS subtitr faylini tashlang');
      return;
    }
    setState(() {
      if (video != null) {
        _selectedVideo = null;
        _externalVideoPath = video;
        _result = null;
        _status = 'Tashlab qo\'yilgan video tanlandi';
      }
      if (subtitle != null) {
        _externalSubtitlePath = subtitle;
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
      setState(() {
        _status = 'Yuklandi: $name';
        _progress = 1;
      });
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
        subtitlePath: _externalSubtitlePath,
        subtitleOffset: _subtitleOffset,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _status = 'Yakunlandi';
        _progress = 1;
      });
      _settingsStore.saveLastResult(result);
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
        subtitlePath: _externalSubtitlePath,
        subtitleOffset: _subtitleOffset,
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
      builder: (_) => _BatchQueueDialog(videos: videos),
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
    final results = <_BatchResult>[];
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
          );
          results.add(_BatchResult(video: v, success: true));
          if (mounted) setState(() => _result = result);
          _settingsStore.saveLastResult(result);
        } on ProcessorCancelled {
          break;
        } catch (error) {
          results.add(
            _BatchResult(video: v, success: false, detail: error.toString()),
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
        builder: (_) => _PlaylistPickerDialog(entries: entries),
      );
      if (selected == null || selected.isEmpty || !mounted) return;
      await _startUrlBatch(selected);
    } catch (error) {
      _showError(error.toString());
    }
  }

  Future<void> _startUrlBatch(List<PlaylistEntry> entries) async {
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
          sub = _result!.outputs
              .where((o) => o.kind == 'ass' || o.kind == 'srt')
              .firstOrNull
              ?.path;
        }
        if (sub == null || !File(sub).existsSync()) {
          final dot = path.lastIndexOf('.');
          if (dot > 0) {
            final base = path.substring(0, dot);
            final ass = '$base.ass';
            final srt = '$base.srt';
            if (File(ass).existsSync()) {
              sub = ass;
            } else if (File(srt).existsSync()) {
              sub = srt;
            }
          }
        }

        await InAppVideoPlayerDialog.show(
          context,
          videoPath: path,
          subtitlePath: sub,
          onOpenExternal: (p) => _service.openPath(p),
        );
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
    final theme = Theme.of(context);

    return DropTarget(
      onDragDone: (detail) => _handleDrop(detail.files),
      child: CallbackShortcuts(
        bindings: <ShortcutActivator, VoidCallback>{
          const SingleActivator(LogicalKeyboardKey.keyO, control: true): () {
            if (!_running) _pickExternalVideo();
          },
          const SingleActivator(LogicalKeyboardKey.keyO, meta: true): () {
            if (!_running) _pickExternalVideo();
          },
          const SingleActivator(LogicalKeyboardKey.enter, control: true): () {
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
            appBar: AppBar(
              titleSpacing: 24,
              toolbarHeight: 70,
              title: Row(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: Image.asset(
                      'assets/app_logo.png',
                      width: 36,
                      height: 36,
                      fit: BoxFit.cover,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Text(
                    'Subtitr Desktop',
                    style: theme.textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.5,
                    ),
                  ),
                  if (_appVersion != null) ...[
                    const SizedBox(width: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 7,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        'v$_appVersion',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
              actions: [
                IconButton(
                  tooltip: _settings.hasAnyKey
                      ? 'API kalitlar (${_settings.configuredProviders.join(", ")})'
                      : 'API kalitlarni kiriting',
                  onPressed: _running ? null : _openSettings,
                  icon: Badge(
                    isLabelVisible: !_settings.hasAnyKey,
                    backgroundColor: Colors.amber,
                    child: const Icon(Icons.key_rounded),
                  ),
                  style: IconButton.styleFrom(
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: 'Paketlarni o\'rnatish',
                  onPressed: _running ? null : _installDependencies,
                  icon: const Icon(Icons.download_for_offline_rounded),
                  style: IconButton.styleFrom(
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: 'Kinolar papkasini ochish',
                  onPressed: _kinoDir.isEmpty
                      ? null
                      : () => _openPath(_kinoDir),
                  icon: const Icon(Icons.folder_open_rounded),
                  style: IconButton.styleFrom(
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  tooltip: 'Tayyor natijalar papkasini ochish',
                  onPressed: _outDir.isEmpty ? null : () => _openPath(_outDir),
                  icon: const Icon(Icons.output_rounded),
                  style: IconButton.styleFrom(
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
                const SizedBox(width: 24),
              ],
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
                    onClearSubtitle: () =>
                        setState(() => _externalSubtitlePath = null),
                    onOffsetChanged: (value) =>
                        setState(() => _subtitleOffset = value),
                    onSelectVideo: (v) {
                      if (v.isDir) {
                        _scanVideos(path: v.path);
                      } else {
                        setState(() {
                          _selectedVideo = v;
                          _externalVideoPath = null;
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
                      });
                      _updateDuration();
                    },
                    onUrlSubmit: _startFromUrl,
                    onDownloadOnly: _downloadOnly,
                    onPlaylistSubmit: _loadPlaylistQueue,
                    onPreviewVideo: _openPath,
                  );

                  final leftColumn = Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      videoPanel,
                      const SizedBox(height: 24),
                      Expanded(
                        child: SettingsPanel(
                          modes: _modes,
                          mode: _mode,
                          sourceLang: _sourceLang,
                          targetLang: _targetLang,
                          appearance: _appearance,
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
                          presets: _presets,
                          onSavePreset: _savePreset,
                          onApplyPreset: _applyPreset,
                          onDeletePreset: _deletePreset,
                        ),
                      ),
                    ],
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
                      : _BatchResultsCard(
                          results: _batchResults,
                          onDetail: _showErrorDetail,
                        );
                  final wideRightColumn = Column(
                    children: [
                      Expanded(child: processor),
                      if (batchCard case final Widget card) card,
                    ],
                  );

                  if (wide) {
                    return Padding(
                      padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          SizedBox(width: 440, child: leftColumn),
                          const SizedBox(width: 24),
                          Container(width: 1, color: const Color(0xFF333333)),
                          const SizedBox(width: 24),
                          Expanded(child: wideRightColumn),
                        ],
                      ),
                    );
                  }

                  return ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                    children: [
                      SizedBox(height: 580, child: leftColumn),
                      const SizedBox(height: 16),
                      processor,
                      if (batchCard case final Widget card) card,
                    ],
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _BatchResult {
  const _BatchResult({
    required this.video,
    required this.success,
    this.detail = '',
  });
  final DesktopVideo video;
  final bool success;
  final String detail;
}

class _BatchQueueDialog extends StatefulWidget {
  const _BatchQueueDialog({required this.videos});
  final List<DesktopVideo> videos;

  @override
  State<_BatchQueueDialog> createState() => _BatchQueueDialogState();
}

class _BatchQueueDialogState extends State<_BatchQueueDialog> {
  late final List<DesktopVideo> _queue = [...widget.videos];
  late final Set<String> _selected = _queue.map((item) => item.path).toSet();

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Ishlash navbati'),
    content: SizedBox(
      width: 560,
      height: 420,
      child: ReorderableListView.builder(
        buildDefaultDragHandles: false,
        itemCount: _queue.length,
        onReorderItem: (oldIndex, newIndex) => setState(() {
          final item = _queue.removeAt(oldIndex);
          _queue.insert(newIndex, item);
        }),
        itemBuilder: (context, index) {
          final video = _queue[index];
          return ListTile(
            key: ValueKey(video.path),
            leading: Checkbox(
              value: _selected.contains(video.path),
              onChanged: (value) => setState(() {
                if (value == true) {
                  _selected.add(video.path);
                } else {
                  _selected.remove(video.path);
                }
              }),
            ),
            title: Text(
              video.name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(
              video.path,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            trailing: ReorderableDragStartListener(
              index: index,
              child: const Icon(Icons.drag_handle_rounded),
            ),
            onTap: () => setState(() {
              if (_selected.contains(video.path)) {
                _selected.remove(video.path);
              } else {
                _selected.add(video.path);
              }
            }),
          );
        },
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Bekor qilish'),
      ),
      FilledButton(
        onPressed: _selected.isEmpty
            ? null
            : () => Navigator.pop(
                context,
                _queue.where((item) => _selected.contains(item.path)).toList(),
              ),
        child: Text('${_selected.length} ta videoni boshlash'),
      ),
    ],
  );
}

class _BatchResultsCard extends StatelessWidget {
  const _BatchResultsCard({required this.results, required this.onDetail});
  final List<_BatchResult> results;
  final ValueChanged<String> onDetail;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(top: 12),
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Navbat natijalari',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          ...results.map(
            (item) => ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                item.success
                    ? Icons.check_circle_outline_rounded
                    : Icons.error_outline_rounded,
                color: item.success
                    ? Colors.green
                    : Theme.of(context).colorScheme.error,
              ),
              title: Text(
                item.video.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: item.success
                  ? null
                  : TextButton(
                      onPressed: () => onDetail(item.detail),
                      child: const Text('Tafsilot'),
                    ),
            ),
          ),
        ],
      ),
    ),
  );
}
