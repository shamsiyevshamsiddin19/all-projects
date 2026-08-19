import 'package:flutter/material.dart';

import '../services/desktop_processor_service.dart';

/// Review-and-edit screen shown between the `prepare` and `render` phases.
///
/// The user sees every subtitle line — the original on top and its editable
/// translation below — and can fix wording before the slow burn step. Popping
/// with the edited [SubtitleSegment] list tells the caller to render; popping
/// with `null` cancels.
class TranslationEditorScreen extends StatefulWidget {
  const TranslationEditorScreen({super.key, required this.session});

  final PreparedSession session;

  @override
  State<TranslationEditorScreen> createState() =>
      _TranslationEditorScreenState();
}

class _TranslationEditorScreenState extends State<TranslationEditorScreen> {
  late final List<TextEditingController> _controllers;
  late final List<SubtitleSegment> _segments;
  String _search = '';

  @override
  void initState() {
    super.initState();
    _segments = widget.session.segments;
    _controllers = _segments
        .map((s) => TextEditingController(text: s.translated))
        .toList();
  }

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    super.dispose();
  }

  List<SubtitleSegment> _collect() {
    for (var i = 0; i < _segments.length; i++) {
      _segments[i].translated = _controllers[i].text;
    }
    return _segments;
  }

  static String _timecode(double seconds) {
    final total = seconds.round();
    final m = (total ~/ 60).toString().padLeft(2, '0');
    final s = (total % 60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  bool _matches(int i) {
    if (_search.isEmpty) return true;
    final q = _search.toLowerCase();
    return _segments[i].original.toLowerCase().contains(q) ||
        _controllers[i].text.toLowerCase().contains(q);
  }

  @override
  Widget build(BuildContext context) {
    final hasTranslation = _segments.any((s) => s.translated.trim().isNotEmpty);
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
            child: TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search, size: 20),
                hintText: 'Qatorlardan qidirish...',
                isDense: true,
              ),
              onChanged: (v) => setState(() => _search = v),
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
              itemCount: visible.length,
              itemBuilder: (context, idx) {
                final i = visible[idx];
                return _SegmentTile(
                  index: i + 1,
                  timecode:
                      '${_timecode(_segments[i].start)} → ${_timecode(_segments[i].end)}',
                  original: _segments[i].original,
                  controller: _controllers[i],
                  editable: hasTranslation,
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

class _SegmentTile extends StatelessWidget {
  const _SegmentTile({
    required this.index,
    required this.timecode,
    required this.original,
    required this.controller,
    required this.editable,
  });

  final int index;
  final String timecode;
  final String original;
  final TextEditingController controller;
  final bool editable;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF222222)),
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
              controller: controller,
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
