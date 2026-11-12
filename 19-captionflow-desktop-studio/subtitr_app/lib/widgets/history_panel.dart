import 'package:flutter/material.dart';

class HistoryEntry {
  const HistoryEntry({
    required this.name,
    required this.directoryPath,
    required this.videoPath,
    required this.subtitlePath,
    required this.modified,
  });

  final String name;
  final String directoryPath;
  final String? videoPath;
  final String? subtitlePath;
  final DateTime modified;
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
  });

  final List<HistoryEntry> items;
  final VoidCallback onClose;
  final void Function(String videoPath) onPlay;
  final void Function(String folderPath) onOpenFolder;
  final VoidCallback onOpenOutputFolder;
  final VoidCallback onRefresh;

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
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  Icons.history_rounded,
                  color: theme.colorScheme.primary,
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
                                          : theme.colorScheme.primary)
                                      .withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Icon(
                                  item.videoPath != null
                                      ? Icons.movie_outlined
                                      : Icons.folder_outlined,
                                  color: item.videoPath != null
                                      ? const Color(0xFF10B981)
                                      : theme.colorScheme.primary,
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
                                child: Row(
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
                                    const SizedBox(width: 8),
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
                                    if (item.subtitlePath != null) ...[
                                      const SizedBox(width: 4),
                                      Container(
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
                                    ],
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
