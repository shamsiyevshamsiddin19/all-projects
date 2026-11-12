import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Ilova ichida hujjatlar (PDF, Word DOCX, Markdown, Matn va Subtitrlar)ni
/// tashqi dasturlarsiz to'g'ridan-to'g'ri o'qish va ko'rish vidjeti.
class DocumentViewer extends StatefulWidget {
  const DocumentViewer({
    super.key,
    required this.filePath,
    this.title,
    required this.onClose,
    this.onOpenExternal,
    this.headerLeading,
  });

  final String filePath;
  final String? title;
  final VoidCallback onClose;
  final ValueChanged<String>? onOpenExternal;
  final Widget? headerLeading;

  @override
  State<DocumentViewer> createState() => _DocumentViewerState();
}

class _DocumentViewerState extends State<DocumentViewer> {
  bool _loading = true;
  String _content = '';
  String? _error;
  double _fontSize = 13.5;
  String _searchQuery = '';
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _copied = false;

  @override
  void initState() {
    super.initState();
    _loadFile();
  }

  @override
  void didUpdateWidget(covariant DocumentViewer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.filePath != widget.filePath) {
      _loadFile();
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadFile() async {
    setState(() {
      _loading = true;
      _error = null;
      _copied = false;
    });

    try {
      final file = File(widget.filePath);
      if (!file.existsSync()) {
        throw Exception('Fayl topilmadi: ${widget.filePath}');
      }

      final lower = widget.filePath.toLowerCase();
      String extracted = '';

      if (lower.endsWith('.pdf')) {
        extracted = await _readPdf(widget.filePath);
      } else if (lower.endsWith('.docx') || lower.endsWith('.doc')) {
        extracted = await _readDocx(widget.filePath);
      } else {
        // .md, .txt, .srt, .ass, .vtt, .json
        extracted = file.readAsStringSync();
      }

      if (mounted) {
        setState(() {
          _content = extracted.trim().isEmpty
              ? '(Fayl bo\'sh yoki matn topilmadi)'
              : extracted;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
          _loading = false;
        });
      }
    }
  }

  Future<String> _readPdf(String path) async {
    try {
      final result = await Process.run('pdftotext', [path, '-']);
      if (result.exitCode == 0 && result.stdout is String) {
        final text = (result.stdout as String).trim();
        if (text.isNotEmpty) return text;
      }
    } catch (_) {}

    // Fallback: Python orqali pypdf/fitz yoki matn o'qish
    try {
      final py = await Process.run('python3', [
        '-c',
        '''
import sys
try:
    from pypdf import PdfReader
    reader = PdfReader(sys.argv[1])
    text = "\\n".join(page.extract_text() or "" for page in reader.pages)
    print(text)
except Exception as e:
    pass
''',
        path,
      ]);
      if (py.exitCode == 0 && py.stdout is String && (py.stdout as String).trim().isNotEmpty) {
        return (py.stdout as String).trim();
      }
    } catch (_) {}

    return 'PDF fayl yuklandi: ${File(path).uri.pathSegments.last}\n(Matn qatlamini ajratib bo\'lmadi)';
  }

  Future<String> _readDocx(String path) async {
    try {
      final result = await Process.run('unzip', ['-p', path, 'word/document.xml']);
      if (result.exitCode == 0 && result.stdout is String) {
        final xml = result.stdout as String;
        final paragraphs = xml.split('</w:p>');
        final buffer = StringBuffer();
        for (final p in paragraphs) {
          final matches = RegExp(r'<w:t[^>]*>(.*?)</w:t>').allMatches(p);
          final line = matches.map((m) => m.group(1) ?? '').join();
          if (line.trim().isNotEmpty) {
            buffer.writeln(line.trim());
          }
        }
        if (buffer.isNotEmpty) return buffer.toString();
      }
    } catch (_) {}

    // Fallback: Python docx
    try {
      final py = await Process.run('python3', [
        '-c',
        '''
import sys
try:
    import docx
    doc = docx.Document(sys.argv[1])
    print("\\n".join(p.text for p in doc.paragraphs if p.text.strip()))
except Exception:
    pass
''',
        path,
      ]);
      if (py.exitCode == 0 && py.stdout is String && (py.stdout as String).trim().isNotEmpty) {
        return (py.stdout as String).trim();
      }
    } catch (_) {}

    return 'DOCX hujjati: ${File(path).uri.pathSegments.last}';
  }

  String get _fileName => File(widget.filePath).uri.pathSegments.last;

  String get _fileBadge {
    final lower = widget.filePath.toLowerCase();
    if (lower.endsWith('.pdf')) return 'PDF';
    if (lower.endsWith('.docx')) return 'DOCX';
    if (lower.endsWith('.doc')) return 'DOC';
    if (lower.endsWith('.md')) return 'MD';
    if (lower.endsWith('.srt')) return 'SRT';
    if (lower.endsWith('.ass')) return 'ASS';
    if (lower.endsWith('.vtt')) return 'VTT';
    if (lower.endsWith('.txt')) return 'TXT';
    return 'DOC';
  }

  Color get _badgeColor {
    final lower = widget.filePath.toLowerCase();
    if (lower.endsWith('.pdf')) return const Color(0xFFEF4444);
    if (lower.endsWith('.docx') || lower.endsWith('.doc')) return const Color(0xFF3B82F6);
    if (lower.endsWith('.md')) return const Color(0xFFA855F7);
    if (lower.endsWith('.srt') || lower.endsWith('.ass')) return const Color(0xFFF59E0B);
    return const Color(0xFF10B981);
  }

  int get _wordCount {
    if (_content.isEmpty) return 0;
    return _content.split(RegExp(r'\s+')).where((s) => s.isNotEmpty).length;
  }

  int get _lineCount {
    if (_content.isEmpty) return 0;
    return _content.split('\n').length;
  }

  void _copyAll() {
    Clipboard.setData(ClipboardData(text: _content));
    setState(() => _copied = true);
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) setState(() => _copied = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F1015),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF22232A)),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          // Yuqori sarlavha paneli
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: const BoxDecoration(
              color: Color(0xFF15161E),
              border: Border(bottom: BorderSide(color: Color(0xFF22232A))),
            ),
            child: Row(
              children: [
                if (widget.headerLeading != null) ...[
                  widget.headerLeading!,
                  const SizedBox(width: 10),
                ],
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                  decoration: BoxDecoration(
                    color: _badgeColor.withValues(alpha: 0.16),
                    borderRadius: BorderRadius.circular(5),
                    border: Border.all(color: _badgeColor.withValues(alpha: 0.35)),
                  ),
                  child: Text(
                    _fileBadge,
                    style: TextStyle(
                      color: _badgeColor,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    widget.title ?? _fileName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                      color: Color(0xFFE2E8F0),
                    ),
                  ),
                ),
                if (widget.onOpenExternal != null)
                  IconButton(
                    tooltip: 'Tashqi dasturda ochish',
                    icon: const Icon(Icons.open_in_new_rounded, size: 18, color: Color(0xFF94A3B8)),
                    onPressed: () => widget.onOpenExternal!(widget.filePath),
                  ),
                IconButton(
                  tooltip: 'Yopish',
                  icon: const Icon(Icons.close_rounded, size: 20, color: Color(0xFF94A3B8)),
                  onPressed: widget.onClose,
                ),
              ],
            ),
          ),

          // Ikkinchi boshqaruv paneli: qidiruv, shrift o'lchami, nusxalash, statistika
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: const BoxDecoration(
              color: Color(0xFF111218),
              border: Border(bottom: BorderSide(color: Color(0xFF1D1E26))),
            ),
            child: Row(
              children: [
                // Qidiruv maydoni
                Expanded(
                  child: SizedBox(
                    height: 32,
                    child: TextField(
                      controller: _searchController,
                      style: const TextStyle(fontSize: 12, color: Color(0xFFE2E8F0)),
                      decoration: InputDecoration(
                        hintText: 'Hujjat ichidan qidirish...',
                        hintStyle: const TextStyle(fontSize: 11.5, color: Color(0xFF64748B)),
                        prefixIcon: const Icon(Icons.search_rounded, size: 16, color: Color(0xFF64748B)),
                        suffixIcon: _searchQuery.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear_rounded, size: 14),
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() => _searchQuery = '');
                                },
                              )
                            : null,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
                        isDense: true,
                        filled: true,
                        fillColor: const Color(0xFF1A1B23),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                          borderSide: BorderSide.none,
                        ),
                      ),
                      onChanged: (v) => setState(() => _searchQuery = v.trim().toLowerCase()),
                    ),
                  ),
                ),
                const SizedBox(width: 12),

                // Statistika
                Text(
                  '$_lineCount qator · $_wordCount so\'z',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                ),
                const SizedBox(width: 8),

                // Shrift o'lchami A- / A+
                IconButton(
                  tooltip: 'Shriftni kichiklashtirish (A-)',
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.text_decrease_rounded, size: 17, color: Color(0xFF94A3B8)),
                  onPressed: _fontSize > 10 ? () => setState(() => _fontSize -= 1.5) : null,
                ),
                Text(
                  '${_fontSize.round()}',
                  style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8), fontWeight: FontWeight.w600),
                ),
                IconButton(
                  tooltip: 'Shriftni kattalashtirish (A+)',
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.text_increase_rounded, size: 17, color: Color(0xFF94A3B8)),
                  onPressed: _fontSize < 24 ? () => setState(() => _fontSize += 1.5) : null,
                ),
                const SizedBox(width: 4),

                // Nusxalash
                FilledButton.tonalIcon(
                  onPressed: _content.isNotEmpty ? _copyAll : null,
                  icon: Icon(_copied ? Icons.check_rounded : Icons.copy_rounded, size: 14),
                  label: Text(_copied ? 'Nusxalandi' : 'Nusxalash'),
                  style: FilledButton.styleFrom(
                    backgroundColor: _copied
                        ? const Color(0xFF10B981).withValues(alpha: 0.2)
                        : const Color(0xFF22232E),
                    foregroundColor: _copied ? const Color(0xFF10B981) : const Color(0xFFCBD5E1),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    textStyle: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            ),
          ),

          // Asosiy matn maydoni
          Expanded(
            child: _loading
                ? const Center(
                    child: CircularProgressIndicator(color: Color(0xFF38BDF8)),
                  )
                : _error != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24.0),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.error_outline_rounded, color: Color(0xFFEF4444), size: 36),
                              const SizedBox(height: 12),
                              Text(
                                'Faylni ochishda xatolik yuz berdi:',
                                style: theme.textTheme.titleSmall?.copyWith(color: const Color(0xFFEF4444)),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                _error!,
                                textAlign: TextAlign.center,
                                style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                              ),
                            ],
                          ),
                        ),
                      )
                    : Scrollbar(
                        controller: _scrollController,
                        thumbVisibility: true,
                        child: SelectionArea(
                          child: SingleChildScrollView(
                            controller: _scrollController,
                            padding: const EdgeInsets.all(24),
                            child: _buildFormattedContent(),
                          ),
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFormattedContent() {
    final lines = _content.split('\n');
    final widgets = <Widget>[];

    for (int i = 0; i < lines.length; i++) {
      final line = lines[i];
      final trimmed = line.trim();

      // Qidiruv bo'lsa faqat mos kelgan qatorlarni ko'rsatamiz
      if (_searchQuery.isNotEmpty && !line.toLowerCase().contains(_searchQuery)) {
        continue;
      }

      if (trimmed.startsWith('# ')) {
        // Asosiy sarlavha
        widgets.add(Padding(
          padding: const EdgeInsets.only(top: 14.0, bottom: 8.0),
          child: Text(
            trimmed.substring(2),
            style: TextStyle(
              fontSize: _fontSize + 5,
              fontWeight: FontWeight.w800,
              color: const Color(0xFF38BDF8),
              letterSpacing: -0.3,
            ),
          ),
        ));
      } else if (trimmed.startsWith('## ') || trimmed.startsWith('### ')) {
        // Quymoy sarlavha
        final hText = trimmed.replaceFirst(RegExp(r'^#+\s*'), '');
        widgets.add(Padding(
          padding: const EdgeInsets.only(top: 10.0, bottom: 6.0),
          child: Text(
            hText,
            style: TextStyle(
              fontSize: _fontSize + 2.5,
              fontWeight: FontWeight.w700,
              color: const Color(0xFFF1F5F9),
            ),
          ),
        ));
      } else if (trimmed.startsWith('::')) {
        // Tarjima qatori
        widgets.add(Container(
          margin: const EdgeInsets.symmetric(vertical: 3),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          decoration: BoxDecoration(
            color: const Color(0xFF10B981).withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(6),
            border: const Border(left: BorderSide(color: Color(0xFF10B981), width: 3)),
          ),
          child: Text(
            trimmed.substring(2).trim(),
            style: TextStyle(
              fontSize: _fontSize,
              fontWeight: FontWeight.w500,
              color: const Color(0xFF34D399),
              height: 1.45,
            ),
          ),
        ));
      } else if (RegExp(r'^\d+\s*$').hasMatch(trimmed) &&
          i + 1 < lines.length &&
          lines[i + 1].contains('-->')) {
        // SRT raqami
        widgets.add(Padding(
          padding: const EdgeInsets.only(top: 12.0),
          child: Text(
            '#$trimmed',
            style: const TextStyle(
              fontSize: 10.5,
              fontWeight: FontWeight.w700,
              color: Color(0xFF64748B),
            ),
          ),
        ));
      } else if (trimmed.contains('-->')) {
        // Subtitr vaqti (SRT / VTT)
        widgets.add(Padding(
          padding: const EdgeInsets.only(bottom: 3.0),
          child: Text(
            trimmed,
            style: TextStyle(
              fontSize: _fontSize - 2,
              fontFamily: 'monospace',
              fontWeight: FontWeight.w600,
              color: const Color(0xFFF59E0B),
            ),
          ),
        ));
      } else if (trimmed.isEmpty) {
        widgets.add(const SizedBox(height: 8));
      } else {
        // Oddiy matn qatori
        widgets.add(Padding(
          padding: const EdgeInsets.symmetric(vertical: 2.0),
          child: Text(
            line,
            style: TextStyle(
              fontSize: _fontSize,
              color: const Color(0xFFE2E8F0),
              height: 1.5,
              backgroundColor: _searchQuery.isNotEmpty
                  ? const Color(0xFFF59E0B).withValues(alpha: 0.25)
                  : null,
            ),
          ),
        ));
      }
    }

    if (widgets.isEmpty && _searchQuery.isNotEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Text(
            '"$_searchQuery" bo\'yicha hech narsa topilmadi',
            style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: widgets,
    );
  }
}
