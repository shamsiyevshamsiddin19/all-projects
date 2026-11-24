import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Video ko'rish holati yozuvi.
class VideoPlaybackRecord {
  const VideoPlaybackRecord({
    required this.positionMs,
    this.durationMs,
    required this.updatedAtMs,
  });

  final int positionMs;
  final int? durationMs;
  final int updatedAtMs;

  Duration get position => Duration(milliseconds: positionMs);
  Duration? get duration =>
      durationMs != null ? Duration(milliseconds: durationMs!) : null;

  Map<String, dynamic> toJson() => {
        'pos_ms': positionMs,
        if (durationMs != null) 'dur_ms': durationMs,
        'ts': updatedAtMs,
      };

  factory VideoPlaybackRecord.fromJson(Map<String, dynamic> json) {
    return VideoPlaybackRecord(
      positionMs: (json['pos_ms'] as num?)?.toInt() ?? 0,
      durationMs: (json['dur_ms'] as num?)?.toInt(),
      updatedAtMs: (json['ts'] as num?)?.toInt() ?? 0,
    );
  }
}

/// Har bir video bo'yicha ko'rish vaqtini eslab qoluvchi xizmat (Playback Resume Store).
///
/// Xususiyatlari:
/// - Xotiradagi (in-memory) tezkor kesh va [SharedPreferences] orqali doimiy saqlash.
/// - 3 soniyadan kam ko'rilgan yoki video oxiriga (duration - 5s) yetgan holatlarda
///   avtomatik ravishda boshidan boshlash.
/// - Kesh hajmi 100 tadan oshganda eng eski yozuvlarni avtomatik tozalash (LRU).
class PlaybackPositionStore {
  static const String prefKey = 'video_playback_positions_v1';
  static const int maxSavedVideos = 100;
  static const int minResumeSeconds = 3;
  static const int endThresholdSeconds = 5;

  static final PlaybackPositionStore instance =
      PlaybackPositionStore._internal();
  PlaybackPositionStore._internal();

  @visibleForTesting
  PlaybackPositionStore.create();

  final Map<String, VideoPlaybackRecord> _cache = {};
  bool _initialized = false;

  /// Xotiradagi keshni [SharedPreferences] dan yuklaydi.
  Future<void> init() async {
    if (_initialized) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(prefKey);
      if (raw != null && raw.isNotEmpty) {
        final decoded = jsonDecode(raw) as Map<String, dynamic>;
        for (final entry in decoded.entries) {
          if (entry.value is Map) {
            _cache[entry.key] = VideoPlaybackRecord.fromJson(
              Map<String, dynamic>.from(entry.value as Map),
            );
          }
        }
      }
    } catch (_) {
      // Buzilgan jsonni xavfsiz o'tkazib yuboramiz
    } finally {
      _initialized = true;
    }
  }

  /// Tezkor xotiradan (in-memory) darhol oxirgi ko'rilgan vaqtni olish.
  Duration? getCachedPosition(String videoPath) {
    final record = _cache[videoPath];
    if (record == null) return null;
    return _filterPosition(record);
  }

  /// Video uchun saqlangan vaqtni olish (kesh yuklanmagan bo'lsa yuklaydi).
  Future<Duration?> getSavedPosition(String videoPath) async {
    if (!_initialized) {
      await init();
    }
    return getCachedPosition(videoPath);
  }

  /// 3s dan kam yoki video oxiriga yaqin bo'lsa null qaytaradi.
  Duration? _filterPosition(VideoPlaybackRecord record) {
    final posSec = record.positionMs / 1000.0;
    if (posSec < minResumeSeconds) {
      return null;
    }
    if (record.durationMs != null) {
      final durSec = record.durationMs! / 1000.0;
      if (durSec > 0 && posSec >= durSec - endThresholdSeconds) {
        return null;
      }
    }
    return record.position;
  }

  /// Video ko'rish holatini saqlash.
  Future<void> savePosition(
    String videoPath,
    Duration position, {
    Duration? duration,
  }) async {
    final posMs = position.inMilliseconds;
    final durMs = duration?.inMilliseconds;
    final posSec = posMs / 1000.0;
    final durSec = durMs != null ? durMs / 1000.0 : null;

    if (posSec < minResumeSeconds ||
        (durSec != null &&
            durSec > 0 &&
            posSec >= durSec - endThresholdSeconds)) {
      await clearPosition(videoPath);
      return;
    }

    final record = VideoPlaybackRecord(
      positionMs: posMs,
      durationMs: durMs,
      updatedAtMs: DateTime.now().millisecondsSinceEpoch,
    );

    _cache[videoPath] = record;
    _pruneCacheIfNeeded();

    await _flushToDisk();
  }

  /// Video tugagach yoki qaytadan boshlash uchun yozuvni o'chirish.
  Future<void> clearPosition(String videoPath) async {
    if (_cache.containsKey(videoPath)) {
      _cache.remove(videoPath);
      await _flushToDisk();
    }
  }

  void _pruneCacheIfNeeded() {
    if (_cache.length <= maxSavedVideos) return;
    final sortedEntries = _cache.entries.toList()
      ..sort((a, b) => a.value.updatedAtMs.compareTo(b.value.updatedAtMs));
    final removeCount = _cache.length - maxSavedVideos;
    for (int i = 0; i < removeCount; i++) {
      _cache.remove(sortedEntries[i].key);
    }
  }

  Future<void> _flushToDisk() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final map = _cache.map((k, v) => MapEntry(k, v.toJson()));
      await prefs.setString(prefKey, jsonEncode(map));
    } catch (_) {}
  }

  @visibleForTesting
  void clearMemoryCache() {
    _cache.clear();
    _initialized = false;
  }
}
