import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
  late final List<({String original, String translated, double start, double end})> _initialState;
  late final bool _showsTranslation;
  String _search = '';
  bool _onlyUncertain = false;
  bool _hasUnsavedChanges = false;
  bool _exitApproved = false;

  /// Qidiruvni kechiktirish taymeri. Har bosilgan harf butun ro'yxatni
  /// qayta quradi — 2000 qatorli kinoda "qidirish" so'zini yozish 8 marta
  /// to'liq qayta qurish degani.
  Timer? _searchDebounce;

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
    _initialState = _segments
        .map(
          (segment) => (
            original: segment.original,
            translated: segment.translated,
            start: segment.start,
            end: segment.end,
          ),
        )
        .toList(growable: false);
    // Tarjima rejimi ish boshlanishidagi tanlovga bog'liq. Foydalanuvchi
    // oxirgi tarjimani vaqtincha o'chirsa, kiritish maydoni yo'qolib ketmasin.
    _showsTranslation = _segments.any(
      (segment) => segment.translated.trim().isNotEmpty,
    );
    if (playerAvailable) _loadPlayer();
  }

  void _onSegmentTextChanged() {
    final changed = _segments.indexed.any((entry) {
      final initial = _initialState[entry.$1];
      final segment = entry.$2;
      return segment.original != initial.original ||
          segment.translated != initial.translated ||
          (segment.start - initial.start).abs() > 0.001 ||
          (segment.end - initial.end).abs() > 0.001;
    });
    // PopScope faqat tahrir holati o'zgarganda qayta qurilishi kerak;
    // har bir harfda butun, katta ro'yxatni qurish sezilarli sekinlashtiradi.
    if (changed != _hasUnsavedChanges) {
      setState(() => _hasUnsavedChanges = changed);
    }
  }

  Future<void> _requestExit() async {
    if (!_hasUnsavedChanges) {
      Navigator.of(context).pop();
      return;
    }

    final discard = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.edit_off_outlined),
        title: const Text('Tahrirlar saqlanmaydi'),
        content: const Text('Chiqilsinmi? Tahrirlar saqlanmaydi.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Qolish'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Chiqish'),
          ),
        ],
      ),
    );
    if (discard != true || !mounted) return;

    for (final entry in _segments.indexed) {
      final initial = _initialState[entry.$1];
      entry.$2.original = initial.original;
      entry.$2.translated = initial.translated;
      entry.$2.start = initial.start;
      entry.$2.end = initial.end;
    }
    // Segmentlar session bilan bir obyektni bo'lishadi. Bekor qilishdan
    // keyin ularni qaytarib qo'yamiz, aks holda `null` natijaga qaramay
    // tahrir keyingi ishlovga sizib o'tishi mumkin.
    setState(() {
      _hasUnsavedChanges = false;
      _exitApproved = true;
    });
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    Navigator.of(context).pop();
  }

  Future<void> _submitEdits() async {
    // Render tugmasi tahrirlarni saqlab qaytadi. PopScope uni bekor qilish
    // chiqishi deb to'xtatmasligi uchun, natijali chiqishni oldindan belgilaymiz.
    setState(() => _exitApproved = true);
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    Navigator.of(context).pop(_collect());
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

  void _onSearchChanged(String value) {
    _searchDebounce?.cancel();
    // Yozish tugaguncha kutamiz; 180 ms — tez yozganda ham sezilmaydi,
    // lekin har harfdagi qayta qurishni to'xtatadi.
    _searchDebounce = Timer(const Duration(milliseconds: 180), () {
      if (mounted) setState(() => _search = value);
    });
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
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
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.error,
          ),
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
        errorBuilder: (context, error, stack) =>
            const Center(child: Text('Kadr ochilmadi')),
      );
    } else {
      body = Center(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(
            'Qatorni bossangiz, subtitr o\'sha joyda qanday '
            'chiqishi shu yerda ko\'rinadi.',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
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
    final hasTranslation = _showsTranslation;
    final uncertain = _segments.where((s) => s.isUncertain).length;
    final visible = <int>[
      for (var i = 0; i < _segments.length; i++)
        if (_matches(i)) i,
    ];

    return CallbackShortcuts(
      bindings: <ShortcutActivator, VoidCallback>{
        const SingleActivator(LogicalKeyboardKey.enter, control: true): _submitEdits,
        const SingleActivator(LogicalKeyboardKey.enter, meta: true): _submitEdits,
        const SingleActivator(LogicalKeyboardKey.escape): _requestExit,
      },
      child: Focus(
        autofocus: true,
        child: PopScope(
      canPop: _exitApproved || !_hasUnsavedChanges,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop && _hasUnsavedChanges) _requestExit();
      },
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Tarjimani ko\'rib chiqish'),
          actions: [
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Center(
                child: Text(
                  '${_segments.length} qator',
                  style: const TextStyle(
                    color: Color(0xFFAAAAAA),
                    fontSize: 13,
                  ),
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
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 12,
                ),
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
                      onChanged: _onSearchChanged,
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
                        segment: _segments[i],
                        editable: hasTranslation,
                        onTextChanged: _onSegmentTextChanged,
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
                    onPressed: _requestExit,
                    child: const Text('Bekor qilish'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: FilledButton.icon(
                    onPressed: _submitEdits,
                    icon: const Icon(Icons.movie_creation_outlined, size: 20),
                    label: const Text('Videoni render qilish'),
                  ),
                ),
              ],
            ),
          ),
        ),
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
    required this.segment,
    required this.editable,
    required this.onTextChanged,
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

  /// Tahrir to'g'ridan-to'g'ri shunga yoziladi.
  final SubtitleSegment segment;

  final bool editable;
  final VoidCallback onTextChanged;

  /// The model was unsure of this line — worth reading before rendering.
  final bool uncertain;

  @override
  State<_SegmentTile> createState() => _SegmentTileState();
}

class _SegmentTileState extends State<_SegmentTile> {
  TextEditingController? _translationController;
  bool _editingOriginal = false;

  TextEditingController get _originalField => _originalController ??=
      TextEditingController(text: widget.segment.original);
  TextEditingController? _originalController;

  TextEditingController get _translationField => _translationController ??=
      TextEditingController(text: widget.segment.translated)
        // Har bosilgan harf segmentga yoziladi, shuning uchun qator
        // ekrandan chiqib ketsa ham tahrir yo'qolmaydi.
        ..addListener(() {
          widget.segment.translated = _translationController!.text;
          widget.onTextChanged();
        });

  @override
  void dispose() {
    _originalController?.dispose();
    _translationController?.dispose();
    super.dispose();
  }

  static String _formatSeconds(double seconds) {
    if (seconds < 0) seconds = 0;
    final total = seconds.floor();
    final m = (total ~/ 60).toString().padLeft(2, '0');
    final s = (total % 60).toString().padLeft(2, '0');
    final ms = ((seconds - total) * 10).floor().toString();
    return '$m:$s.$ms';
  }

  static double? _parseTime(String input) {
    final s = input.trim();
    if (s.isEmpty) return null;
    if (s.contains(':')) {
      final parts = s.split(':');
      if (parts.length == 2) {
        final m = double.tryParse(parts[0]);
        final sec = double.tryParse(parts[1]);
        if (m != null && sec != null) return m * 60 + sec;
      } else if (parts.length == 3) {
        final h = double.tryParse(parts[0]);
        final m = double.tryParse(parts[1]);
        final sec = double.tryParse(parts[2]);
        if (h != null && m != null && sec != null) return h * 3600 + m * 60 + sec;
      }
    }
    return double.tryParse(s);
  }

  Future<void> _editTiming() async {
    final startController = TextEditingController(
      text: _formatSeconds(widget.segment.start),
    );
    final endController = TextEditingController(
      text: _formatSeconds(widget.segment.end),
    );

    double currentStart = widget.segment.start;
    double currentEnd = widget.segment.end;

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) {
          void updateFields(double newStart, double newEnd) {
            if (newStart < 0) newStart = 0;
            if (newEnd <= newStart) newEnd = newStart + 0.1;
            currentStart = double.parse(newStart.toStringAsFixed(3));
            currentEnd = double.parse(newEnd.toStringAsFixed(3));
            startController.text = _formatSeconds(currentStart);
            endController.text = _formatSeconds(currentEnd);
            setDialogState(() {});
          }

          void shiftBoth(double delta) {
            final duration = currentEnd - currentStart;
            var newStart = currentStart + delta;
            if (newStart < 0) newStart = 0;
            final newEnd = newStart + duration;
            updateFields(newStart, newEnd);
          }

          return AlertDialog(
            icon: const Icon(Icons.access_time_rounded),
            title: Text('Vaqtni sozlash (#${widget.index})'),
            content: SizedBox(
              width: 380,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          key: const ValueKey('start-time-field'),
                          controller: startController,
                          decoration: const InputDecoration(
                            labelText: 'Boshlanish',
                            hintText: '00:00.0',
                            isDense: true,
                          ),
                          onChanged: (val) {
                            final p = _parseTime(val);
                            if (p != null) currentStart = p;
                          },
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          key: const ValueKey('end-time-field'),
                          controller: endController,
                          decoration: const InputDecoration(
                            labelText: 'Tugash',
                            hintText: '00:00.0',
                            isDense: true,
                          ),
                          onChanged: (val) {
                            final p = _parseTime(val);
                            if (p != null) currentEnd = p;
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Tezkor sozlash (surish):',
                    style: TextStyle(fontSize: 12, color: Color(0xFF888888)),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: [
                      ActionChip(
                        label: const Text('-0.5s ikkalasi'),
                        onPressed: () => shiftBoth(-0.5),
                      ),
                      ActionChip(
                        label: const Text('+0.5s ikkalasi'),
                        onPressed: () => shiftBoth(0.5),
                      ),
                      ActionChip(
                        label: const Text('-0.2s start'),
                        onPressed: () => updateFields(currentStart - 0.2, currentEnd),
                      ),
                      ActionChip(
                        label: const Text('+0.2s start'),
                        onPressed: () => updateFields(currentStart + 0.2, currentEnd),
                      ),
                      ActionChip(
                        label: const Text('-0.2s end'),
                        onPressed: () => updateFields(currentStart, currentEnd - 0.2),
                      ),
                      ActionChip(
                        label: const Text('+0.2s end'),
                        onPressed: () => updateFields(currentStart, currentEnd + 0.2),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(false),
                child: const Text('Bekor qilish'),
              ),
              FilledButton(
                key: const ValueKey('save-timing-button'),
                onPressed: () {
                  final pStart = _parseTime(startController.text) ?? currentStart;
                  final pEnd = _parseTime(endController.text) ?? currentEnd;
                  if (pEnd > pStart && pStart >= 0) {
                    currentStart = double.parse(pStart.toStringAsFixed(3));
                    currentEnd = double.parse(pEnd.toStringAsFixed(3));
                    Navigator.of(ctx).pop(true);
                  }
                },
                child: const Text('Saqlash'),
              ),
            ],
          );
        },
      ),
    );

    if (saved == true && mounted) {
      widget.segment.start = currentStart;
      widget.segment.end = currentEnd;
      widget.onTextChanged();
      setState(() {});
    }
  }

  @override
  Widget build(BuildContext context) {
    final index = widget.index;
    // timecode dinamik hisoblanadi
    final editable = widget.editable;
    final uncertain = widget.uncertain;
    final selected = widget.selected;
    final onPreview = widget.onPreview;
    final borderColor = selected
        ? Colors.white
        : (uncertain
              ? Colors.amber.withValues(alpha: 0.6)
              : const Color(0xFF222222));
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
              const SizedBox(width: 8),
              Tooltip(
                message: "Vaqtni o'zgartirish (boshlanish va tugash)",
                child: InkWell(
                  key: ValueKey('timing-tile-${widget.index}'),
                  onTap: _editTiming,
                  borderRadius: BorderRadius.circular(6),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.access_time_rounded,
                          size: 13,
                          color: Color(0xFF888888),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${_formatSeconds(widget.segment.start)} → ${_formatSeconds(widget.segment.end)}',
                          style: const TextStyle(
                            color: Color(0xFFAAAAAA),
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Icon(
                          Icons.edit_outlined,
                          size: 12,
                          color: Color(0xFF666666),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const Spacer(),
              if (onPreview != null)
                IconButton(
                  tooltip: 'Shu joydan ko\'rish',
                  onPressed: onPreview,
                  visualDensity: VisualDensity.compact,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(
                    minWidth: 30,
                    minHeight: 30,
                  ),
                  icon: Icon(
                    Icons.image_outlined,
                    size: 17,
                    color: selected ? Colors.white : const Color(0xFF777777),
                  ),
                ),
              if (uncertain) ...[
                const SizedBox(width: 4),
                Icon(
                  Icons.help_outline_rounded,
                  size: 15,
                  color: Colors.amber.withValues(alpha: 0.9),
                ),
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
          if (editable)
            // Daraxtda tarjima birinchi turadi, lekin `up` yo'nalishi uni
            // pastga joylaydi. Shu yo'l bilan ikkala matn ham Material
            // maydon bo'ladi va original foydalanuvchi ko'radigan yuqorida.
            Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              verticalDirection: VerticalDirection.up,
              children: [
                TextField(
                  controller: _translationField,
                  maxLines: null,
                  style: const TextStyle(fontSize: 14, height: 1.35),
                  decoration: const InputDecoration(
                    isDense: true,
                    hintText: 'Tarjima...',
                    contentPadding: EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 12,
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                _originalEditor(index),
              ],
            )
          else
            _originalEditor(index),
        ],
      ),
    );
  }

  Widget _originalTextField(int index) => TextField(
    key: ValueKey('original-$index'),
    controller: _originalField,
    maxLines: null,
    style: const TextStyle(
      color: Color(0xFFCCCCCC),
      fontSize: 14,
      height: 1.35,
    ),
    decoration: const InputDecoration(
      labelText: 'Asl matn',
      isDense: true,
      contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    ),
    onChanged: (text) {
      // Transkripsiya ism yoki atamani noto'g'ri eshitganda foydalanuvchi
      // aynan asl jumlani tuzatib render qiladi.
      widget.segment.original = text;
      widget.onTextChanged();
    },
  );

  Widget _originalEditor(int index) {
    if (_editingOriginal) return _originalTextField(index);
    return Tooltip(
      message: 'Asl matnni tahrirlash',
      child: InkWell(
        onTap: () => setState(() => _editingOriginal = true),
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  widget.segment.original.isEmpty
                      ? 'Asl matn kiritish'
                      : widget.segment.original,
                  style: const TextStyle(
                    color: Color(0xFFCCCCCC),
                    fontSize: 14,
                    height: 1.35,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Icon(
                Icons.edit_outlined,
                size: 16,
                color: Color(0xFF888888),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
