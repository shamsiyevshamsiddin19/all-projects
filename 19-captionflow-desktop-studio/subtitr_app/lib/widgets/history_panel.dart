import 'package:flutter/material.dart';

import '../models/studio_media_file.dart';

class HistoryEntry {
  const HistoryEntry({
    required this.name,
    required this.directoryPath,
    required this.videoPath,
    required this.subtitlePath,
    required this.modified,
    this.files = const [],
    this.rawName = '',
  });

  final String name;
  final String directoryPath;
  final String? videoPath;
  final String? subtitlePath;
  final DateTime modified;
  final List<StudioMediaFile> files;
  final String rawName;
}

class HistoryPanel extends StatefulWidget {
  const HistoryPanel({
    super.key,
    required this.items,
    required this.onClose,
    required this.onPlay,
    required this.onOpenFolder,
    required this.onOpenOutputFolder,
    required this.onRefresh,
    this.onDelete,
  });

  final List<HistoryEntry> items;
  final VoidCallback onClose;
  final void Function(String videoPath) onPlay;
  final void Function(String folderPath) onOpenFolder;
  final VoidCallback onOpenOutputFolder;
  final VoidCallback onRefresh;
  final Future<void> Function(HistoryEntry entry)? onDelete;

  @override
  State<HistoryPanel> createState() => _HistoryPanelState();
}

class _HistoryPanelState extends State<HistoryPanel> {
  final TextEditingController _searchController = TextEditingController();
  String _search = '';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final timeStr =
        '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    if (dt.year == now.year && dt.month == now.month && dt.day == now.day) {
      return 'Bugun, $timeStr';
    }
    final yesterday = now.subtract(const Duration(days: 1));
    if (dt.year == yesterday.year &&
        dt.month == yesterday.month &&
        dt.day == yesterday.day) {
      return 'Kecha, $timeStr';
    }
    const months = [
      'yanvar',
      'fevral',
      'mart',
      'aprel',
      'may',
      'iyun',
      'iyul',
      'avgust',
      'sentabr',
      'oktabr',
      'noyabr',
      'dekabr',
    ];
    return '${dt.day}-${months[dt.month - 1]}, $timeStr';
  }

  Future<void> _confirmDelete(BuildContext context, HistoryEntry item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF141414),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xFF333333)),
        ),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.redAccent.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.delete_forever_rounded,
                color: Colors.redAccent,
                size: 22,
              ),
            ),
            const SizedBox(width: 12),
            const Text(
              'Tozalash',
              style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '"${item.name}" videoning barcha natijalari va keshlangan fayllari butunlay o\'chiriladi.',
              style: const TextStyle(fontSize: 14, height: 1.4),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.black45,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF262626)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.folder_outlined, size: 16, color: Colors.grey),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      item.directoryPath,
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              "Haqiqatan ham kesh va natijalarni tozalab o'chirmoqchimisiz?",
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.redAccent,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Bekor qilish'),
          ),
          FilledButton.icon(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.redAccent,
              foregroundColor: Colors.white,
            ),
            icon: const Icon(Icons.delete_outline_rounded, size: 18),
            label: const Text("O'chirish"),
            onPressed: () => Navigator.pop(ctx, true),
          ),
        ],
      ),
    );

    if (confirmed == true && widget.onDelete != null) {
      await widget.onDelete!(item);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filtered = widget.items.where((i) {
      if (_search.isEmpty) return true;
      return i.name.toLowerCase().contains(_search.toLowerCase());
    }).toList();

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
        ),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A1A),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF2E2E2E)),
                ),
                child: const Icon(
                  Icons.history_rounded,
                  color: Color(0xFFFBBF24),
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          'Jarayonlar tarixi',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.2,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${widget.items.length}',
                            style: theme.textTheme.labelSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: theme.colorScheme.primary,
                            ),
                          ),
                        ),
                      ],
                    ),
                    Text(
                      'Avval tayyorlangan video va subtitrlar',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Yangilash',
                icon: const Icon(Icons.refresh_rounded, size: 20),
                onPressed: widget.onRefresh,
              ),
              IconButton(
                tooltip: 'Barcha natijalar papkasi',
                icon: const Icon(Icons.folder_open_rounded, size: 20),
                onPressed: widget.onOpenOutputFolder,
              ),
              const SizedBox(width: 4),
              IconButton(
                tooltip: 'Yopish',
                icon: const Icon(Icons.close_rounded, size: 20),
                onPressed: widget.onClose,
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (widget.items.length >= 3) ...[
            TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Tarixdan qidirish...',
                prefixIcon: const Icon(Icons.search_rounded, size: 18),
                suffixIcon: _search.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear_rounded, size: 16),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _search = '');
                        },
                      )
                    : null,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 10,
                ),
                isDense: true,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: BorderSide(
                    color: theme.colorScheme.outlineVariant.withValues(
                      alpha: 0.4,
                    ),
                  ),
                ),
              ),
              onChanged: (v) => setState(() => _search = v.trim()),
            ),
            const SizedBox(height: 12),
          ],
          Expanded(
            child: widget.items.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.history_toggle_off_rounded,
                          size: 56,
                          color: theme.colorScheme.outline.withValues(
                            alpha: 0.5,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Hali yakunlangan natijalar yo\'q',
                          style: theme.textTheme.bodyLarge?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Video qayta ishlangach, natijalar shu yerda ko\'rinadi.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  )
                : filtered.isEmpty
                    ? const Center(
                        child: Text(
                          'Qidiruv bo\'yicha natija topilmadi',
                          style: TextStyle(color: Colors.grey),
                        ),
                      )
                    : ListView.separated(
                        itemCount: filtered.length,
                        separatorBuilder: (_, _) => const SizedBox(height: 8),
                        itemBuilder: (context, index) {
                          final item = filtered[index];
                          return Container(
                            decoration: BoxDecoration(
                              color: theme.colorScheme.surfaceContainerHighest
                                  .withValues(alpha: 0.35),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: theme.colorScheme.outlineVariant
                                    .withValues(alpha: 0.2),
                              ),
                            ),
                            child: ListTile(
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 4,
                              ),
                              leading: Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  color: (item.videoPath != null
                                          ? const Color(0xFF10B981)
                                          : (item.files.any((f) => f.category == StudioFileCategory.pdf)
                                              ? const Color(0xFFEF4444)
                                              : theme.colorScheme.primary))
                                      .withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Icon(
                                  item.videoPath != null
                                      ? Icons.movie_outlined
                                      : (item.files.any((f) => f.isDocument)
                                          ? Icons.description_outlined
                                          : Icons.folder_outlined),
                                  color: item.videoPath != null
                                      ? const Color(0xFF10B981)
                                      : (item.files.any((f) => f.category == StudioFileCategory.pdf)
                                          ? const Color(0xFFEF4444)
                                          : theme.colorScheme.primary),
                                  size: 22,
                                ),
                              ),
                              title: Text(
                                item.name,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13,
                                ),
                              ),
                              subtitle: Padding(
                                padding: const EdgeInsets.only(top: 4.0),
                                child: Wrap(
                                  spacing: 4,
                                  runSpacing: 4,
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  children: [
                                    Text(
                                      _formatDate(item.modified),
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: theme
                                            .colorScheme
                                            .onSurfaceVariant,
                                      ),
                                    ),
                                    const SizedBox(width: 4),
                                    if (item.videoPath != null)
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 6,
                                          vertical: 1,
                                        ),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFF10B981)
                                              .withValues(alpha: 0.15),
                                          borderRadius: BorderRadius.circular(
                                            4,
                                          ),
                                        ),
                                        child: const Text(
                                          'VIDEO',
                                          style: TextStyle(
                                            fontSize: 9.5,
                                            fontWeight: FontWeight.w700,
                                            color: Color(0xFF10B981),
                                          ),
                                        ),
                                      ),
                                    if (item.subtitlePath != null)
                                      InkWell(
                                        onTap: () => widget.onPlay(item.subtitlePath!),
                                        borderRadius: BorderRadius.circular(4),
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 6,
                                            vertical: 1,
                                          ),
                                          decoration: BoxDecoration(
                                            color: theme.colorScheme.primary
                                                .withValues(alpha: 0.15),
                                            borderRadius: BorderRadius.circular(
                                              4,
                                            ),
                                            border: Border.all(
                                              color: theme.colorScheme.primary
                                                  .withValues(alpha: 0.3),
                                            ),
                                          ),
                                          child: Text(
                                            item.subtitlePath!.toLowerCase()
                                                    .endsWith('.ass')
                                                ? 'ASS'
                                                : 'SRT',
                                            style: TextStyle(
                                              fontSize: 9.5,
                                              fontWeight: FontWeight.w700,
                                              color: theme.colorScheme.primary,
                                            ),
                                          ),
                                        ),
                                      ),
                                    // Boshqa materiallar (PDF, DOCX, MD, ASS, SRT)
                                    for (final f in item.files.where((f) =>
                                        f.category == StudioFileCategory.pdf ||
                                        f.category == StudioFileCategory.docx ||
                                        f.category == StudioFileCategory.markdown ||
                                        (f.category == StudioFileCategory.subtitle && f.path != item.subtitlePath)))
                                      InkWell(
                                        onTap: () => widget.onPlay(f.path),
                                        borderRadius: BorderRadius.circular(4),
                                        child: Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 5,
                                            vertical: 1,
                                          ),
                                          decoration: BoxDecoration(
                                            color: f.color.withValues(alpha: 0.15),
                                            borderRadius: BorderRadius.circular(4),
                                            border: Border.all(
                                              color: f.color.withValues(alpha: 0.3),
                                            ),
                                          ),
                                          child: Text(
                                            f.badgeText,
                                            style: TextStyle(
                                              fontSize: 9.5,
                                              fontWeight: FontWeight.w700,
                                              color: f.color,
                                            ),
                                          ),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  if (item.videoPath != null)
                                    IconButton(
                                      icon: const Icon(
                                        Icons.play_circle_fill_rounded,
                                        color: Color(0xFF10B981),
                                        size: 26,
                                      ),
                                      tooltip: 'Ilova pleyerida ko\'rish',
                                      onPressed: () =>
                                          widget.onPlay(item.videoPath!),
                                    )
                                  else if (item.files.isNotEmpty)
                                    IconButton(
                                      icon: const Icon(
                                        Icons.visibility_rounded,
                                        color: Color(0xFF38BDF8),
                                        size: 24,
                                      ),
                                      tooltip: 'Materiallarni o\'qish',
                                      onPressed: () =>
                                          widget.onPlay(item.files.first.path),
                                    ),
                                  IconButton(
                                    icon: const Icon(
                                      Icons.folder_open_rounded,
                                      size: 20,
                                    ),
                                    tooltip: 'Papkani ochish',
                                    onPressed: () => widget.onOpenFolder(
                                      item.directoryPath,
                                    ),
                                  ),
                                  if (widget.onDelete != null)
                                    IconButton(
                                      icon: const Icon(
                                        Icons.delete_outline_rounded,
                                        color: Color(0xFFEF4444),
                                        size: 20,
                                      ),
                                      tooltip: 'Tozalash (Kesh va natijalarni o\'chirish)',
                                      onPressed: () =>
                                          _confirmDelete(context, item),
                                    ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
