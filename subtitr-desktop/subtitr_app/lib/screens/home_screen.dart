import 'dart:async';
import 'dart:io';import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../services/desktop_processor_service.dart';
import '../services/settings_store.dart';
import '../widgets/processing_panel.dart';
import '../widgets/settings_panel.dart';
import '../widgets/video_selection_panel.dart';
import 'api_keys_screen.dart';
import 'translation_editor_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.autoScan = true});

  final bool autoScan;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final DesktopProcessorService _service = DesktopProcessorService();
  final SettingsStore _settingsStore = SettingsStore();
  AppSettings _settings = const AppSettings();
  AppearanceSettings _appearance = const AppearanceSettings();
  String _batchInfo = ''; // "Video 2/5" — navbat holati

  List<DesktopVideo> _videos = const [];
  DesktopVideo? _selectedVideo;
  ProcessorResult? _result;
  String? _externalVideoPath;
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
    _loadSettings();
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
    _service.processEnvironment = settings.toEnvironment();
    if (mounted) {
      setState(() {
        _settings = settings;
        _appearance = appearance;
        _mode = job['mode'] ?? _mode;
        _sourceLang = job['source'] ?? _sourceLang;
        _targetLang = job['target'] ?? _targetLang;
      });
    }
  }

  void _saveJobPrefs() {
    _settingsStore.saveJobPrefs(mode: _mode, source: _sourceLang, target: _targetLang);
  }

  void _updateAppearance(AppearanceSettings a) {
    setState(() => _appearance = a);
    _settingsStore.saveAppearance(a);
  }

  Future<void> _openSettings() async {
    final updated = await Navigator.of(context).push<AppSettings>(
      MaterialPageRoute(
        builder: (_) => ApiKeysScreen(initial: _settings),
      ),
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
  Future<void> _downloadOnly(String url) async {
    setState(() {
      _running = true;
      _result = null;
      _progress = 0;
      _status = 'Video yuklab olinmoqda';
      _startTime = DateTime.now();
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
    try {
      final res = await _service.downloadUrl(url: url, onProgress: _applyProgress);
      if (!mounted) return;
      final dir = res['dir'] as String? ?? '';
      final name = res['name'] as String? ?? 'video';
      setState(() {
        _status = 'Yuklandi: $name';
        _progress = 1;
      });
      if (dir.isNotEmpty) await _openPath(dir);
    } on ProcessorCancelled {
      if (mounted) setState(() { _status = 'Bekor qilindi'; _progress = 0; });
    } catch (error) {
      _showError(error.toString());
    } finally {
      _timer?.cancel();
      if (mounted) setState(() { _running = false; _startTime = null; });
    }
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
        
        if (_selectedVideo != null && !_videos.any((v) => v.path == _selectedVideo!.path)) {
          _selectedVideo = null;
        }
        if (_selectedVideo == null) {
          final firstFile = _videos.where((v) => !v.isDir).firstOrNull;
          _selectedVideo = firstFile;
        }

        _externalVideoPath = null;
        _status = _videos.isEmpty ? 'Kinolar papkasiga video tashlang' : 'Tayyor';
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
    _timer?.cancel();
    super.dispose();
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
    setState(() {
      _running = true;
      _result = null;
      _progress = 0;
      _status = 'Boshlanmoqda';
      _startTime = DateTime.now();
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
    try {
      final result = await _service.process(
        videoPath: path,
        mode: _mode,
        sourceLang: _sourceLang,
        targetLang: _targetLang,
        onProgress: _applyProgress,
        fontScale: _appearance.fontScale,
        position: _appearance.position,
        subColor: _appearance.subColor,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _status = 'Yakunlandi';
        _progress = 1;
      });
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
    setState(() {
      _running = true;
      _result = null;
      _progress = 0;
      _status = 'Matn tayyorlanmoqda';
      _startTime = DateTime.now();
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });

    PreparedSession? session;
    try {
      session = await _service.prepare(
        videoPath: path,
        mode: _mode,
        sourceLang: _sourceLang,
        targetLang: _targetLang,
        onProgress: _applyProgress,
      );
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
    if (session == null || !mounted) return;

    // Review/edit screen — returns edited segments, or null if cancelled.
    final edited = await Navigator.of(context).push<List<SubtitleSegment>>(
      MaterialPageRoute(
        builder: (_) => TranslationEditorScreen(session: session!),
      ),
    );
    if (edited == null || !mounted) {
      setState(() => _status = 'Tayyor');
      return;
    }

    // Phase 2 — render the edited translation.
    setState(() {
      _running = true;
      _result = null;
      _progress = 0;
      _status = 'Render qilinmoqda';
      _startTime = DateTime.now();
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
    try {
      final result = await _service.render(
        sessionPath: session.sessionPath,
        segments: edited,
        onProgress: _applyProgress,
        fontScale: _appearance.fontScale,
        position: _appearance.position,
        subColor: _appearance.subColor,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _status = 'Yakunlandi';
        _progress = 1;
      });
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
    _batchCancelled = false;
    setState(() {
      _running = true;
      _result = null;
    });
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) setState(() {});
    });
    int done = 0;
    int failed = 0;
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
          );
          done++;
          if (mounted) setState(() => _result = result);
        } on ProcessorCancelled {
          break;
        } catch (_) {
          failed++;
        }
      }
      if (mounted) {
        setState(() {
          _progress = _batchCancelled ? 0 : 1;
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
      _progress = progress.progress.clamp(0, 1);
    });
  }

  Future<void> _openPath(String path) async {
    try {
      await _service.openPath(path);
    } catch (error) {
      _showError(error.toString());
    }
  }

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
    if (_mode == 'srt' || _mode == 'transcript') factor = 0.15;
    return (_videoDuration * factor).round();
  }

  /// Rough token estimate so the user knows about how much they'll spend.
  String get _estimateText {
    if (_videoDuration <= 0) return '';
    final segs = (_videoDuration / 3.5).round();
    const needsTr = true; // deyarli barcha rejimlar tarjima qiladi
    final needsVocab = _mode.contains('vocab') || _mode == 'vocabulary' || _mode == 'all';
    var tokens = 0;
    if (needsTr && _mode != 'vocabulary') tokens += segs * 45;
    if (needsVocab) tokens += segs * 25;
    if (tokens <= 0) return '~$segs subtitr';
    final k = (tokens / 1000).round();
    return '~$segs subtitr · ~$k ming token';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
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
            onPressed: _kinoDir.isEmpty ? null : () => _openPath(_kinoDir),
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
                    isRunning: _running,
                    isLoading: _loading,
                    onScan: () => _scanVideos(path: _currentDir),
                    onPickExternal: _pickExternalVideo,
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
                        _selectedVideo = _videos.where((v) => !v.isDir).firstOrNull;
                      });
                      _updateDuration();
                    },
                    onUrlSubmit: _startFromUrl,
                    onDownloadOnly: _downloadOnly,
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
                          onModeChanged: (v) { setState(() => _mode = v); _saveJobPrefs(); },
                          onSourceLangChanged: (v) { setState(() => _sourceLang = v); _saveJobPrefs(); },
                          onTargetLangChanged: (v) { setState(() => _targetLang = v); _saveJobPrefs(); },
                          onAppearanceChanged: _updateAppearance,
                        ),
                      ),
                    ],
                  );

                  final rightColumn = ProcessingPanel(
                    selectedName: _selectedName,
                    selectedPath: _selectedPath,
                    outDir: _result?.outDir.isNotEmpty == true ? _result!.outDir : _outDir,
                    isRunning: _running,
                    progress: _progress,
                    status: _status,
                    result: _result,
                    estimatedSeconds: _estimatedSeconds,
                    estimateText: _estimateText,
                    startTime: _startTime,
                    onStart: _startProcessing,
                    onReview: _reviewAndRender,
                    onCancel: _cancelProcessing,
                    onStartBatch: _startBatch,
                    videoCount: _videos.where((v) => !v.isDir).length,
                    onOpenPath: _openPath,
                  );

                  if (wide) {
                    return Padding(
                      padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          SizedBox(
                            width: 440,
                            child: leftColumn,
                          ),
                          const SizedBox(width: 24),
                          Container(width: 1, color: const Color(0xFF333333)),
                          const SizedBox(width: 24),
                          Expanded(
                            child: rightColumn,
                          ),
                        ],
                      ),
                    );
                  }

                  return ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                    children: [
                      SizedBox(height: 580, child: leftColumn),
                      const SizedBox(height: 16),
                      rightColumn,
                    ],
                  );
                },
              ),
      ),
    );
  }
}
