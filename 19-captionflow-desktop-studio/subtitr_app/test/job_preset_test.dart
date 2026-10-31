import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:subtitr_app/services/settings_store.dart';

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('preset retains every non-secret processing choice', () async {
    final store = SettingsStore();
    const preset = JobPreset(
      name: 'Dars 1080p',
      mode: 'dual_vocab',
      source: 'ru',
      target: 'uz',
      subtitleOffset: -2,
      appearance: AppearanceSettings(
        fontScale: 1.2,
        position: 'top',
        subColor: '#FFFFFF',
        origStyle: 'plain',
        quality: '1080',
        upscale: true,
      ),
    );

    await store.savePreset(preset);
    final saved = await store.loadPresets();

    expect(saved, hasLength(1));
    expect(saved.single.name, 'Dars 1080p');
    expect(saved.single.source, 'ru');
    expect(saved.single.appearance.quality, '1080');
    expect(saved.single.appearance.upscale, isTrue);
    expect(saved.single.subtitleOffset, -2);
  });

  test(
    'a same-named preset replaces the former version and can be deleted',
    () async {
      final store = SettingsStore();
      const base = JobPreset(
        name: 'Kino',
        mode: 'dual',
        source: 'auto',
        target: 'uz',
        appearance: AppearanceSettings(),
        subtitleOffset: 0,
      );
      await store.savePreset(base);
      await store.savePreset(
        const JobPreset(
          name: 'kino',
          mode: 'translated',
          source: 'en',
          target: 'uz',
          appearance: AppearanceSettings(quality: '2160'),
          subtitleOffset: 5,
        ),
      );
      expect((await store.loadPresets()).single.mode, 'translated');

      await store.deletePreset('kino');
      expect(await store.loadPresets(), isEmpty);
    },
  );
}
