import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

enum ProcessLogLevel {
  info,
  success,
  warning,
  error,
}

class ProcessLogEntry {
  const ProcessLogEntry({
    required this.timestamp,
    required this.message,
    this.progress,
    this.level = ProcessLogLevel.info,
  });

  final DateTime timestamp;
  final String message;
  final double? progress;
  final ProcessLogLevel level;

  String get formattedTime {
    final h = timestamp.hour.toString().padLeft(2, '0');
    final m = timestamp.minute.toString().padLeft(2, '0');
    final s = timestamp.second.toString().padLeft(2, '0');
    return '$h:$m:$s';
  }

  Color get color {
    switch (level) {
      case ProcessLogLevel.success:
        return const Color(0xFF4ADE80);
      case ProcessLogLevel.warning:
        return const Color(0xFFFBBF24);
      case ProcessLogLevel.error:
        return const Color(0xFFF87171);
      case ProcessLogLevel.info:
        return const Color(0xFFE2E8F0);
    }
  }
}

/// Jonli jarayon loglari va tizim terminal konsoli.
///
/// Ushbu vidjet orqali foydalanuvchi video tayyorlanish jarayonidagi
/// barcha qadamlar, FFmpeg, Whisper, AI tarjima va xatoliklarni real
/// vaqtda kuzatib turishi mumkin.
class ProcessLogsConsole extends StatefulWidget {
  const ProcessLogsConsole({
    super.key,
    required this.liveLogs,
    this.isRunning = false,
    this.onLoadDiskLogs,
    this.onOpenLogFile,
    this.onOpenLogDir,
    this.onClearLogs,
    this.onClose,
    this.onExpand,
    this.embedded = false,
  });

  final List<ProcessLogEntry> liveLogs;
  final bool isRunning;
  final Future<String> Function()? onLoadDiskLogs;
  final VoidCallback? onOpenLogFile;
  final VoidCallback? onOpenLogDir;
  final VoidCallback? onClearLogs;
  final VoidCallback? onClose;
  final VoidCallback? onExpand;
  final bool embedded;

  @override
  State<ProcessLogsConsole> createState() => _ProcessLogsConsoleState();
}

class _ProcessLogsConsoleState extends State<ProcessLogsConsole> {
  final ScrollController _scrollController = ScrollController();
  final TextEditingController _filterController = TextEditingController();
  int _selectedTab = 0; // 0: Jonli qadamlar, 1: Tizim log fayli
  bool _autoScroll = true;
  String _diskLogContent = '';
  bool _loadingDiskLogs = false;
  String _filterText = '';

  @override
  void initState() {
    super.initState();
    _filterController.addListener(() {
      setState(() => _filterText = _filterController.text.trim().toLowerCase());
    });
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
  }

  @override
  void didUpdateWidget(covariant ProcessLogsConsole oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.liveLogs.length != oldWidget.liveLogs.length && _autoScroll && _selectedTab == 0) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _filterController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (!_scrollController.hasClients) return;
    _scrollController.animateTo(
      _scrollController.position.maxScrollExtent,
      duration: const Duration(milliseconds: 200),
      curve: Curves.easeOut,
    );
  }

  Future<void> _fetchDiskLogs() async {
    if (widget.onLoadDiskLogs == null) return;
    setState(() => _loadingDiskLogs = true);
    try {
      final content = await widget.onLoadDiskLogs!();
      if (mounted) {
        setState(() {
          _diskLogContent = content.isEmpty ? "Hozircha tizim log faylida yozuvlar yo'q." : content;
          _loadingDiskLogs = false;
        });
        WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _diskLogContent = "Log faylini o'qishda xatolik: $e";
          _loadingDiskLogs = false;
        });
      }
    }
  }

  void _copyAllToClipboard() {
    final String textToCopy;
    if (_selectedTab == 0) {
      textToCopy = widget.liveLogs.map((e) {
        final p = e.progress != null ? ' [${(e.progress! * 100).round()}%]' : '';
        return '[${e.formattedTime}]$p ${e.message}';
      }).join('\n');
    } else {
      textToCopy = _diskLogContent;
    }
    Clipboard.setData(ClipboardData(text: textToCopy));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Loglar buferga nusxalandi'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filteredLiveLogs = _filterText.isEmpty
        ? widget.liveLogs
        : widget.liveLogs.where((e) => e.message.toLowerCase().contains(_filterText)).toList();

    return Container(
      height: widget.embedded ? 320 : null,
      decoration: BoxDecoration(
        color: const Color(0xFF090A0F),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF1E2230)),
        boxShadow: const [
          BoxShadow(
            color: Colors.black45,
            blurRadius: 16,
            offset: Offset(0, 4),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. Yuqori sarlavha paneli (Header)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: const BoxDecoration(
              color: Color(0xFF10121A),
              border: Border(bottom: BorderSide(color: Color(0xFF1E2230))),
            ),
            child: Row(
              children: [
                // Terminal ikonkasi
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E293B),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Icon(
                    Icons.terminal_rounded,
                    size: 16,
                    color: Color(0xFF38BDF8),
                  ),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Jarayon loglari',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFFF1F5F9),
                  ),
                ),
                const SizedBox(width: 8),

                // Jonli status indikatori
                if (widget.isRunning) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: const Color(0xFF14532D),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFF22C55E).withValues(alpha: 0.4)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(
                            color: Color(0xFF22C55E),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Text(
                          'JONLI',
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF86EFAC),
                            letterSpacing: 0.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                ],

                // Yozuvlar soni
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E2230),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '${widget.liveLogs.length} ta satr',
                    style: const TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF94A3B8),
                    ),
                  ),
                ),

                const Spacer(),

                // Tablar: Jonli / Tizim fayli
                SegmentedButton<int>(
                  segments: const [
                    ButtonSegment(
                      value: 0,
                      label: Text('Jonli qadamlar', style: TextStyle(fontSize: 11)),
                    ),
                    ButtonSegment(
                      value: 1,
                      label: Text('Tizim fayli', style: TextStyle(fontSize: 11)),
                    ),
                  ],
                  selected: {_selectedTab},
                  onSelectionChanged: (set) {
                    setState(() => _selectedTab = set.first);
                    if (_selectedTab == 1 && _diskLogContent.isEmpty) {
                      _fetchDiskLogs();
                    }
                  },
                  style: SegmentedButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    backgroundColor: const Color(0xFF0C0E14),
                    selectedBackgroundColor: const Color(0xFF1E293B),
                    selectedForegroundColor: const Color(0xFF38BDF8),
                  ),
                ),
                const SizedBox(width: 8),

                // Qidirish / Filtr
                SizedBox(
                  width: 140,
                  height: 30,
                  child: TextField(
                    controller: _filterController,
                    style: const TextStyle(fontSize: 11, color: Color(0xFFE2E8F0)),
                    decoration: InputDecoration(
                      hintText: 'Filtrlash...',
                      hintStyle: const TextStyle(fontSize: 11, color: Color(0xFF64748B)),
                      prefixIcon: const Icon(Icons.search_rounded, size: 14, color: Color(0xFF64748B)),
                      contentPadding: EdgeInsets.zero,
                      filled: true,
                      fillColor: const Color(0xFF0C0E14),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(6),
                        borderSide: const BorderSide(color: Color(0xFF1E2230)),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(6),
                        borderSide: const BorderSide(color: Color(0xFF1E2230)),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Nusxalash
                IconButton(
                  tooltip: 'Buferga nusxalash',
                  onPressed: _copyAllToClipboard,
                  icon: const Icon(Icons.content_copy_rounded, size: 16, color: Color(0xFF94A3B8)),
                  visualDensity: VisualDensity.compact,
                ),

                // Diskdagi log faylini tashqi muharrirda ochish
                if (widget.onOpenLogFile != null)
                  IconButton(
                    tooltip: 'Log faylini ochish',
                    onPressed: widget.onOpenLogFile,
                    icon: const Icon(Icons.open_in_new_rounded, size: 16, color: Color(0xFF94A3B8)),
                    visualDensity: VisualDensity.compact,
                  ),

                // Loglar papkasini ochish
                if (widget.onOpenLogDir != null)
                  IconButton(
                    tooltip: 'Loglar papkasini ochish',
                    onPressed: widget.onOpenLogDir,
                    icon: const Icon(Icons.folder_open_rounded, size: 16, color: Color(0xFF94A3B8)),
                    visualDensity: VisualDensity.compact,
                  ),

                // Tozalash
                if (widget.onClearLogs != null)
                  IconButton(
                    tooltip: 'Tozalash',
                    onPressed: widget.onClearLogs,
                    icon: const Icon(Icons.delete_sweep_outlined, size: 16, color: Color(0xFF94A3B8)),
                    visualDensity: VisualDensity.compact,
                  ),

                // Kengaytirish (Modal)
                if (widget.embedded && widget.onExpand != null)
                  IconButton(
                    tooltip: 'Kattalashtirish (Oyna)',
                    onPressed: widget.onExpand,
                    icon: const Icon(Icons.fullscreen_rounded, size: 18, color: Color(0xFF94A3B8)),
                    visualDensity: VisualDensity.compact,
                  ),

                // Yopish
                if (widget.onClose != null)
                  IconButton(
                    tooltip: 'Yopish',
                    onPressed: widget.onClose,
                    icon: const Icon(Icons.close_rounded, size: 16, color: Color(0xFF94A3B8)),
                    visualDensity: VisualDensity.compact,
                  ),
              ],
            ),
          ),

          // 2. Terminal maydoni
          Expanded(
            child: _selectedTab == 0
                ? _buildLiveStreamView(filteredLiveLogs)
                : _buildDiskLogView(),
          ),

          // 3. Pastki holat paneli (Footer)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            decoration: const BoxDecoration(
              color: Color(0xFF0C0E14),
              border: Border(top: BorderSide(color: Color(0xFF1E2230))),
            ),
            child: Row(
              children: [
                InkWell(
                  onTap: () {
                    setState(() => _autoScroll = !_autoScroll);
                    if (_autoScroll) _scrollToBottom();
                  },
                  child: Row(
                    children: [
                      Icon(
                        _autoScroll ? Icons.check_box_rounded : Icons.check_box_outline_blank_rounded,
                        size: 14,
                        color: _autoScroll ? const Color(0xFF38BDF8) : const Color(0xFF64748B),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        'Avto-skroll',
                        style: TextStyle(
                          fontSize: 10,
                          color: _autoScroll ? const Color(0xFFE2E8F0) : const Color(0xFF64748B),
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                if (_selectedTab == 1)
                  InkWell(
                    onTap: _fetchDiskLogs,
                    child: Row(
                      children: const [
                        Icon(Icons.refresh_rounded, size: 14, color: Color(0xFF38BDF8)),
                        SizedBox(width: 4),
                        Text(
                          'Faylni yangilash',
                          style: TextStyle(fontSize: 10, color: Color(0xFF38BDF8)),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveStreamView(List<ProcessLogEntry> logs) {
    if (logs.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.terminal_rounded, size: 36, color: Color(0xFF334155)),
              const SizedBox(height: 10),
              Text(
                widget.isRunning
                    ? 'Jarayon qadamlari kutilmoqda...'
                    : '> Hozircha loglar mavjud emas.\nBoshlash tugmasi bosilgach, barcha qadamlar shu yerda jonli ko\'rinadi.',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                  color: Color(0xFF64748B),
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return SelectionArea(
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        itemCount: logs.length,
        itemBuilder: (context, index) {
          final item = logs[index];
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 2.5),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Vaqt
                Text(
                  '[${item.formattedTime}]',
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 11,
                    color: Color(0xFF64748B),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(width: 8),

                // Foiz ko'rsatkichi
                if (item.progress != null) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 0.5),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1E293B),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      '${(item.progress! * 100).round()}%',
                      style: const TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF38BDF8),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],

                // Log matni
                Expanded(
                  child: Text(
                    item.message,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12,
                      color: item.color,
                      height: 1.35,
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDiskLogView() {
    if (_loadingDiskLogs) {
      return const Center(
        child: SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
      );
    }

    if (_diskLogContent.isEmpty) {
      return Center(
        child: OutlinedButton.icon(
          onPressed: _fetchDiskLogs,
          icon: const Icon(Icons.download_rounded, size: 16),
          label: const Text('Log faylini yuklash'),
        ),
      );
    }

    final lines = _diskLogContent.split('\n');
    final filteredLines = _filterText.isEmpty
        ? lines
        : lines.where((l) => l.toLowerCase().contains(_filterText)).toList();

    return SelectionArea(
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        itemCount: filteredLines.length,
        itemBuilder: (context, index) {
          final line = filteredLines[index];
          Color lineColor = const Color(0xFFCBD5E1);
          if (line.contains('ERROR') || line.contains('xato') || line.contains('Traceback')) {
            lineColor = const Color(0xFFF87171);
          } else if (line.contains('WARNING')) {
            lineColor = const Color(0xFFFBBF24);
          } else if (line.contains('--- buyruq:')) {
            lineColor = const Color(0xFF38BDF8);
          }

          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 1.5),
            child: Text(
              line,
              style: TextStyle(
                fontFamily: 'monospace',
                fontSize: 11,
                color: lineColor,
                height: 1.35,
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Jarayon loglarini alohida to'liq modal oynada ochish funksiyasi.
Future<void> showProcessLogsDialog({
  required BuildContext context,
  required List<ProcessLogEntry> liveLogs,
  bool isRunning = false,
  Future<String> Function()? onLoadDiskLogs,
  VoidCallback? onOpenLogFile,
  VoidCallback? onOpenLogDir,
  VoidCallback? onClearLogs,
}) {
  return showDialog<void>(
    context: context,
    builder: (ctx) {
      final size = MediaQuery.sizeOf(ctx);
      final width = (size.width * 0.85).clamp(600.0, 1100.0);
      final height = (size.height * 0.85).clamp(420.0, 780.0);

      return Dialog(
        backgroundColor: Colors.transparent,
        insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        child: SizedBox(
          width: width,
          height: height,
          child: ProcessLogsConsole(
            liveLogs: liveLogs,
            isRunning: isRunning,
            onLoadDiskLogs: onLoadDiskLogs,
            onOpenLogFile: onOpenLogFile,
            onOpenLogDir: onOpenLogDir,
            onClearLogs: onClearLogs,
            onClose: () => Navigator.of(ctx).pop(),
            embedded: false,
          ),
        ),
      );
    },
  );
}
