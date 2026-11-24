import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:subtitr_app/services/playback_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('PlaybackPositionStore', () {
    test('saves and retrieves position when >= 3 seconds', () async {
      final store = PlaybackPositionStore.create();
      const video = '/movies/matrix.mp4';

      await store.savePosition(
        video,
        const Duration(seconds: 45),
        duration: const Duration(seconds: 120),
      );

      final pos = await store.getSavedPosition(video);
      expect(pos, equals(const Duration(seconds: 45)));
    });

    test('ignores positions less than 3 seconds', () async {
      final store = PlaybackPositionStore.create();
      const video = '/movies/matrix.mp4';

      await store.savePosition(
        video,
        const Duration(seconds: 2),
        duration: const Duration(seconds: 120),
      );

      final pos = await store.getSavedPosition(video);
      expect(pos, isNull);
    });

    test('clears position if position is near the end (pos >= duration - 5s)', () async {
      final store = PlaybackPositionStore.create();
      const video = '/movies/matrix.mp4';

      // First save a valid mid-point position
      await store.savePosition(
        video,
        const Duration(seconds: 50),
        duration: const Duration(seconds: 100),
      );
      expect(await store.getSavedPosition(video), equals(const Duration(seconds: 50)));

      // Video reaches 96 seconds of a 100-second video (within 5s of end)
      await store.savePosition(
        video,
        const Duration(seconds: 96),
        duration: const Duration(seconds: 100),
      );

      // Should be cleared so it restarts from 0 next time
      final pos = await store.getSavedPosition(video);
      expect(pos, isNull);
    });

    test('clearPosition removes entry from memory and disk', () async {
      final store = PlaybackPositionStore.create();
      const video = '/movies/avatar.mp4';

      await store.savePosition(
        video,
        const Duration(seconds: 300),
        duration: const Duration(seconds: 1000),
      );

      expect(await store.getSavedPosition(video), equals(const Duration(seconds: 300)));

      await store.clearPosition(video);
      expect(await store.getSavedPosition(video), isNull);
    });

    test('persists to SharedPreferences and reloads on new store instance', () async {
      final store1 = PlaybackPositionStore.create();
      const video = '/movies/interstellar.mp4';

      await store1.savePosition(
        video,
        const Duration(minutes: 15, seconds: 30),
        duration: const Duration(hours: 2),
      );

      final store2 = PlaybackPositionStore.create();
      final pos = await store2.getSavedPosition(video);
      expect(pos, equals(const Duration(minutes: 15, seconds: 30)));
    });

    test('handles corrupt JSON in SharedPreferences gracefully', () async {
      SharedPreferences.setMockInitialValues({
        PlaybackPositionStore.prefKey: 'invalid-not-json{[[',
      });

      final store = PlaybackPositionStore.create();
      final pos = await store.getSavedPosition('/movies/any.mp4');
      expect(pos, isNull);
    });

    test('VideoPlaybackRecord JSON roundtrip', () {
      const record = VideoPlaybackRecord(
        positionMs: 65432,
        durationMs: 120000,
        updatedAtMs: 1716380000,
      );

      final json = record.toJson();
      final restored = VideoPlaybackRecord.fromJson(json);

      expect(restored.positionMs, equals(65432));
      expect(restored.durationMs, equals(120000));
      expect(restored.updatedAtMs, equals(1716380000));
      expect(restored.position, equals(const Duration(milliseconds: 65432)));
      expect(restored.duration, equals(const Duration(milliseconds: 120000)));
    });
  });
}
