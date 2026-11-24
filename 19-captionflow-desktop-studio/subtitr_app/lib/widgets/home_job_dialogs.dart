import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/desktop_processor_service.dart';

/// Playlistdan tanlangan videolarni navbatga qo'shish dialogi.
class PlaylistPickerDialog extends StatefulWidget {
  const PlaylistPickerDialog({super.key, required this.entries});

  final List<PlaylistEntry> entries;

  @override
  State<PlaylistPickerDialog> createState() => _PlaylistPickerDialogState();
}

class _PlaylistPickerDialogState extends State<PlaylistPickerDialog> {
  late final Set<String> _selected = widget.entries
      .map((entry) => entry.url)
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
              if (checked != true) _selected.remove(entry.url);
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
                widget.entries
                    .where((entry) => _selected.contains(entry.url))
                    .toList(),
              ),
        child: Text('${_selected.length} ta navbatga qo\'shish'),
      ),
    ],
  );
}

/// Batch natijasining UI uchun ixcham modeli.
class BatchResult {
  const BatchResult({
    required this.video,
    required this.success,
    this.detail = '',
  });

  final DesktopVideo video;
  final bool success;
  final String detail;
}

/// Batch ishlashdan avval video tanlash va tartibni belgilash dialogi.
class BatchQueueDialog extends StatefulWidget {
  const BatchQueueDialog({super.key, required this.videos});

  final List<DesktopVideo> videos;

  @override
  State<BatchQueueDialog> createState() => _BatchQueueDialogState();
}

class _BatchQueueDialogState extends State<BatchQueueDialog> {
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
        // ignore: deprecated_member_use
        onReorder: (oldIndex, newIndex) => setState(() {
          // Standart ReorderableListView qoidasi: agar element pastga surilsa,
          // olib tashlangandan so'ng indeks 1 ga siljiydi.
          if (oldIndex < newIndex) {
            newIndex -= 1;
          }
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

/// Batchdagi yakunlangan va xato bergan elementlarni ko'rsatadi.
class BatchResultsCard extends StatelessWidget {
  const BatchResultsCard({
    super.key,
    required this.results,
    required this.onDetail,
  });

  final List<BatchResult> results;
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

/// Xabar va hodisalar jurnali elementi.
class AppNotificationRecord {
  const AppNotificationRecord({
    required this.message,
    required this.isError,
    required this.time,
  });

  final String message;
  final bool isError;
  final DateTime time;
}

/// Xatolik tafsilotini ko'rsatish va nusxa olish dialogi.
class ErrorDetailDialog extends StatelessWidget {
  const ErrorDetailDialog({
    super.key,
    required this.message,
    this.onOpenLogs,
  });

  final String message;
  final VoidCallback? onOpenLogs;

  @override
  Widget build(BuildContext context) => AlertDialog(
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
      if (onOpenLogs != null)
        TextButton.icon(
          onPressed: () {
            Navigator.of(context).pop();
            onOpenLogs!();
          },
          icon: const Icon(Icons.folder_open_rounded, size: 18),
          label: const Text('Loglarni ochish'),
        ),
      FilledButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('Yopish'),
      ),
    ],
  );
}

/// Tizim bildirishnomalari dialogi.
class NotificationsDialog extends StatelessWidget {
  const NotificationsDialog({
    super.key,
    required this.notifications,
    required this.onClear,
  });

  final List<AppNotificationRecord> notifications;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Bildirishnomalar'),
    content: SizedBox(
      width: 420,
      child: notifications.isEmpty
          ? const Text('Hali bildirishnoma yo\'q.')
          : ListView.separated(
              shrinkWrap: true,
              itemCount: notifications.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (_, index) {
                final item = notifications[index];
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
      if (notifications.isNotEmpty)
        TextButton(
          onPressed: () {
            onClear();
            Navigator.of(context).pop();
          },
          child: const Text('Tozalash'),
        ),
      FilledButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('Yopish'),
      ),
    ],
  );
}

