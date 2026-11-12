import 'package:flutter/material.dart';

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
        onReorderItem: (oldIndex, newIndex) => setState(() {
          // Yangi Flutter API indeksi element olib tashlangan holatga mos
          // beriladi, shuning uchun pastga ko'chirishda qo'shimcha tuzatish
          // talab qilinmaydi.
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
