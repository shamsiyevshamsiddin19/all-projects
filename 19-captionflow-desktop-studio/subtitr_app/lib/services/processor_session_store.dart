import 'dart:convert';
import 'dart:io';

/// Owns the small JSON files created while a subtitle session is edited.
class ProcessorSessionStore {
  const ProcessorSessionStore({Directory? temporaryDirectory})
    : _temporaryDirectory = temporaryDirectory;

  final Directory? _temporaryDirectory;
  Directory get _temp => _temporaryDirectory ?? Directory.systemTemp;

  File draftFile(String sessionPath) => File('$sessionPath.draft.json');

  Future<File> writeSegments(
    String prefix,
    List<Map<String, dynamic>> segments,
  ) async {
    final file = File(
      '${_temp.path}${Platform.pathSeparator}'
      '$prefix${DateTime.now().microsecondsSinceEpoch}.json',
    );
    await file.writeAsString(jsonEncode(segments), flush: true);
    return file;
  }

  Future<void> saveDraft({
    required String sessionPath,
    required List<Map<String, dynamic>> segments,
  }) async {
    final draft = draftFile(sessionPath);
    await draft.parent.create(recursive: true);
    final temporary = File(
      '${draft.path}.${DateTime.now().microsecondsSinceEpoch}.tmp',
    );
    try {
      await temporary.writeAsString(
        jsonEncode({
          'version': 1,
          'session': sessionPath,
          'segments': segments,
        }),
        flush: true,
      );
      if (await draft.exists()) await draft.delete();
      await temporary.rename(draft.path);
    } finally {
      await deleteQuietly(temporary);
    }
  }

  Future<List<Map<String, dynamic>>?> loadDraft({
    required String sessionPath,
    required int expectedSegments,
  }) async {
    final draft = draftFile(sessionPath);
    try {
      if (!await draft.exists()) return null;
      final decoded = jsonDecode(await draft.readAsString());
      if (decoded is! Map ||
          decoded['version'] != 1 ||
          decoded['session'] != sessionPath) {
        return null;
      }
      final raw = decoded['segments'];
      if (raw is! List || raw.length != expectedSegments) return null;
      final values = raw
          .whereType<Map>()
          .map((value) => Map<String, dynamic>.from(value))
          .toList();
      return values.length == expectedSegments ? values : null;
    } catch (_) {
      return null;
    }
  }

  Future<void> deleteQuietly(File file) async {
    try {
      if (await file.exists()) await file.delete();
    } catch (_) {}
  }
}
