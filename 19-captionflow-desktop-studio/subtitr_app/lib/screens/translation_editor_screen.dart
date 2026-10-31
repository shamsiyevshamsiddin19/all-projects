import 'dart:io';

import 'package:flutter/material.dart';

import '../services/desktop_processor_service.dart';
import '../services/settings_store.dart';
import '../widgets/subtitle_player.dart';

/// Review-and-edit screen shown between the `prepare` and `render` phases.
///
/// The user sees every subtitle line — the original on top and its editable
/// translation below — and can fix wording before the slow burn step. Popping
/// with the edited [SubtitleSegment] list tells the caller to render; popping
/// with `null` cancels.
class TranslationEditorScreen extends StatefulWidget {
  const TranslationEditorScreen({
    super.key,
    required this.session,
    this.appearance = const AppearanceSettings(),
    this.service,
  });

  final PreparedSession session;

  /// Subtitle look, so the preview frame matches what will be burned.
  final AppearanceSettings appearance;

  /// Injected in tests; the screen makes its own otherwise.
  final DesktopProcessorService? service;

  @override
  State<TranslationEditorScreen> createState() =>
      _TranslationEditorScreenState();
}

class _TranslationEditorScreenState extends State<TranslationEditorScreen> {
  late final List<SubtitleSegment> _segments;
  String _search = '';
  bool _onlyUncertain = false;

  late final DesktopProcessorService _service =
      widget.service ?? DesktopProcessorService();

  int? _previewIndex;
  String? _previewPath;
  String? _previewError;
  bool _previewLoading = false;

  /// Guards against a slow preview landing after a newer one was requested.
  int _previewRun = 0;

  // Pleyer: mpv subtitrni o'zi chizadi, shuning uchun jonli ko'rish
  // kuydiriladiganiga aynan mos keladi. Ishga tushmasa (libmpv yo'q,
  // kodek qo'llanmaydi) kadr ko'rishga qaytamiz — u faqat ffmpeg talab
  // qiladi va har doim ishlaydi.
  final SubtitlePlayerController _playerControl = SubtitlePlayerController();
  String? _playerVideo;
  String? _playerSubtitles;
  bool _playerFailed = false;

  bool get _usePlayer =>
      playerAvailable && !_playerFailed && _playerVideo != null;

  @override
  void initState() {
    super.initState();
    _segments = widget.session.segments;
    if (playerAvailable) _loadPlayer();
  }

  /// Writes the ASS once and points the player at it.
  Future<void> _loadPlayer() async {
    try {
      final files = await _service.subtitleFile(
        sessionPath: widget.session.sessionPath,
        segments: _collect(),
        mode: widget.session.mode,
        fontScale: widget.appearance.fontScale,
        position: widget.appearance.position,
        subColor: widget.appearance.subColor,
        origStyle: widget.appearance.origStyle,
      );
      if (!mounted || files.video.isEmpty) return;
      setState(() {
        _playerVideo = files.video;
        _playerSubtitles = files.subtitles;
      });
    } catch (_) {
      if (mounted) setState(() => _playerFailed = true);
    }
  }

  @override
  void dispose() {
    // Kontrollerlar endi har qatorning O'ZIDA — `_SegmentTile` ularni
    // o'zi yaratadi va o'zi tozalaydi.
    super.dispose();
  }

  @override
  void deactivate() {
    // Oynadan chiqilganda ovoz davom etmasin.
    _playerControl.pause();
    super.deactivate();
  }

  /// Renders the frame for [index] with the real subtitle on it.
  ///
  /// Mid-segment, so the line is definitely on screen: at the exact start
  /// the previous subtitle may still be showing.
  Future<void> _preview(int index) async {
    final segment0 = _segments[index];
    if (_usePlayer) {
      setState(() => _previewIndex = index);
      // O'rtasiga sakraymiz: boshida oldingi subtitr hali turgan bo'lishi
      // mumkin.
      final middle = (segment0.start + segment0.end) / 2;
      await _playerControl.seek(
        Duration(milliseconds: (middle * 1000).round()),
      );
      return;
    }
    final run = ++_previewRun;
    setState(() {
      _previewIndex = index;
      _previewLoading = true;
      _previewError = null;
    });
    final segment = _segments[index];
    try {
      final path = await _service.previewFrame(
        sessionPath: widget.session.sessionPath,
        segments: _collect(),
        at: (segment.start + segment.end) / 2,
        mode: widget.session.mode,
        fontScale: widget.appearance.fontScale,
        position: widget.appearance.position,
        subColor: widget.appearance.subColor,
        origStyle: widget.appearance.origStyle,
      );
      if (!mounted || run != _previewRun) return;
      setState(() {
        _previewPath = path;
        _previewLoading = false;
      });
    } catch (error) {
      if (!mounted || run != _previewRun) return;
      setState(() {
        _previewError = error.toString();
        _previewLoading = false;
      });
    }
  }

  Widget _previewPanel() {
    final theme = Theme.of(context);
    if (_usePlayer) {
      return Container(
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF222222)),
        ),
        clipBehavior: Clip.antiAlias,
        child: SubtitlePlayer(
          videoPath: _playerVideo!,
          subtitlePath: _playerSubtitles!,
          controller: _playerControl,
          onUnavailable: (_) {
            if (mounted) setState(() => _playerFailed = true);
          },
        ),
      );
    }
    Widget body;
    if (_previewError != null) {
      body = Padding(
        padding: const EdgeInsets.all(12),
        child: Text(
          _previewError!,
          maxLines: 4,
          overflow: TextOverflow.ellipsis,
          style: theme.textTheme.bodySmall
              ?.copyWith(color: theme.colorScheme.error),
        ),
      );
    } else if (_previewPath != null) {
      // Kesh o'chiriladi: har kadr yangi fayl, lekin Flutter rasmni yo'l
      // bo'yicha keshlaydi — tahrirdan keyin eskisi ko'rinib qolmasin.
      body = Image.file(
        File(_previewPath!),
        key: ValueKey(_previewPath),
        fit: BoxFit.contain,
        gaplessPlayback: true,
        errorBuilder: (context, error, stack) => const Center(child: Text('Kadr ochilmadi')),
      );
    } else {
      body = Center(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'Qatorni bossangiz, subtitr o\'sha joyda qanday '
            'chiqishi shu yerda ko\'rinadi.',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodySmall
                ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
          ),
        ),
      );
    }
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF222222)),
      ),
      clipBehavior: Clip.antiAlias,
      child: Stack(
        fit: StackFit.expand,
        children: [
          body,
          if (_previewLoading)
            const Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: EdgeInsets.all(10),
                child: SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Tahrirlangan matn `_SegmentTile` tomonidan har o'zgarishda
  /// segmentga yoziladi, shuning uchun bu yerda yig'ish shart emas.
  List<SubtitleSegment> _collect() => _segments;

  static String _timecode(double seconds) {
    final total = seconds.round();
    final m = (total ~/ 60).toString().padLeft(2, '0');
    final s = (total % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  bool _matches(int i) {
    if (_onlyUncertain && !_segments[i].isUncertain) return false;
    if (_search.isEmpty) return true;
    final q = _search.toLowerCase();
    return _segments[i].original.toLowerCase().contains(q) ||
        _segments[i].translated.toLowerCase().contains(q);
  }

  @override
  Widget build(BuildContext context) {
    final hasTranslation = _segments.any((s) => s.translated.trim().isNotEmpty);
    final uncertain = _segments.where((s) => s.isUncertain).length;
    final visible = <int>[
      for (var i = 0; i < _segments.length; i++)
        if (_matches(i)) i,
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tarjimani ko\'rib chiqish'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: Text(
                '${_segments.length} qator',
                style: const TextStyle(color: Color(0xFFAAAAAA), fontSize: 13),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          if (!hasTranslation)
            Container(
              width: double.infinity,
              color: const Color(0xFF141414),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: const Text(
                'Bu rejimda tarjima yo\'q — faqat original matnni ko\'rib chiqasiz.',
                style: TextStyle(color: Color(0xFFAAAAAA), fontSize: 13),
              ),
            ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search, size: 20),
                      hintText: 'Qatorlardan qidirish...',
                      isDense: true,
                    ),
                    onChanged: (v) => setState(() => _search = v),
                  ),
                ),
                if (uncertain > 0) ...[
                  const SizedBox(width: 12),
                  // Model ishonmagan qatorlar — noto'g'ri eshitilgan ism
                  // yoki so'z odatda aynan shu joylarda bo'ladi.
                  FilterChip(
                    avatar: Icon(
                      Icons.help_outline_rounded,
                      size: 18,
                      color: _onlyUncertain ? Colors.black : Colors.amber,
                    ),
                    label: Text('Shubhali $uncertain'),
                    selected: _onlyUncertain,
                    selectedColor: Colors.amber,
                    onSelected: (v) => setState(() => _onlyUncertain = v),
                  ),
                ],
              ],
            ),
          ),
          Expanded(
            child: LayoutBuilder(
              builder: (context, constraints) {
                final list = ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                  itemCount: visible.length,
                  itemBuilder: (context, idx) {
                    final i = visible[idx];
                    return _SegmentTile(
                      index: i + 1,
                      timecode:
                          '${_timecode(_segments[i].start)} → ${_timecode(_segments[i].end)}',
                      original: _segments[i].original,
                      segment: _segments[i],
                      editable: hasTranslation,
                      uncertain: _segments[i].isUncertain,
                      selected: _previewIndex == i,
                      onPreview: () => _preview(i),
                    );
                  },
                );
                // Keng oynada kadr yonma-yon turadi — qatorni bosganda
                // ro'yxat joyidan qimirlamaydi.
                if (constraints.maxWidth < 900) return list;
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: list),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(0, 4, 16, 24),
                      child: SizedBox(
                        width: 320,
                        child: AspectRatio(
                          aspectRatio: 9 / 16,
                          child: _previewPanel(),
                        ),
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Bekor qilish'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: FilledButton.icon(
                  onPressed: () => Navigator.of(context).pop(_collect()),
                  icon: const Icon(Icons.movie_creation_outlined, size: 20),
                  label: const Text('Videoni render qilish'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// One subtitle line in the editor.
///
/// Stateful so it can own its own TextEditingController. The screen used to
/// build one controller per line up front: a two-hour film is about 2000
/// lines, so that was 2000 controllers and 2000 pieces of field state alive
/// at once, for the ten or so rows actually on screen. Now a controller
/// exists only while its row is built, and the edited text is written
/// straight back to the segment so nothing is lost when the row scrolls away.
class _SegmentTile extends StatefulWidget {
  const _SegmentTile({
    required this.index,
    required this.timecode,
    required this.original,
    required this.segment,
    required this.editable,
    this.uncertain = false,
    this.selected = false,
    this.onPreview,
  });

  /// This line's frame is the one being shown.
  final bool selected;

  /// Ask for a preview frame at this line.
  final VoidCallback? onPreview;

  final int index;
  final String timecode;
  final String original;

  /// Tahrir to'g'ridan-to'g'ri shunga yoziladi.
  final SubtitleSegment segment;

  final bool editable;

  /// The model was unsure of this line — worth reading before rendering.
  final bool uncertain;

  @override
  State<_SegmentTile> createState() => _SegmentTileState();
}

class _SegmentTileState extends State<_SegmentTile> {
  TextEditingController? _controller;

  TextEditingController get _field =>
      _controller ??= TextEditingController(text: widget.segment.translated)
        // Har bosilgan harf segmentga yoziladi, shuning uchun qator
        // ekrandan chiqib ketsa ham tahrir yo'qolmaydi.
        ..addListener(() => widget.segment.translated = _controller!.text);

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final index = widget.index;
    final timecode = widget.timecode;
    final original = widget.original;
    final editable = widget.editable;
    final uncertain = widget.uncertain;
    final selected = widget.selected;
    final onPreview = widget.onPreview;
    final borderColor = selected
        ? Colors.white
        : (uncertain ? Colors.amber.withValues(alpha: 0.6) : const Color(0xFF222222));
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: selected ? 1.5 : 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '#$index',
                style: const TextStyle(
                  color: Color(0xFF888888),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 10),
              Text(
                timecode,
                style: const TextStyle(color: Color(0xFF666666), fontSize: 12),
              ),
              const Spacer(),
              if (onPreview != null)
                IconButton(
                  tooltip: 'Shu joydan ko\'rish',
                  onPressed: onPreview,
                  visualDensity: VisualDensity.compact,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 30, minHeight: 30),
                  icon: Icon(
                    Icons.image_outlined,
                    size: 17,
                    color: selected ? Colors.white : const Color(0xFF777777),
                  ),
                ),
              if (uncertain) ...[
                const SizedBox(width: 4),
                Icon(Icons.help_outline_rounded,
                     size: 15, color: Colors.amber.withValues(alpha: 0.9)),
                const SizedBox(width: 5),
                Text(
                  'tekshiring',
                  style: TextStyle(
                    color: Colors.amber.withValues(alpha: 0.9),
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 8),
          Text(
            original,
            style: const TextStyle(
              color: Color(0xFFCCCCCC),
              fontSize: 14,
              height: 1.35,
            ),
          ),
          if (editable) ...[
            const SizedBox(height: 10),
            TextField(
              controller: _field,
              maxLines: null,
              style: const TextStyle(fontSize: 14, height: 1.35),
              decoration: const InputDecoration(
                isDense: true,
                hintText: 'Tarjima...',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
