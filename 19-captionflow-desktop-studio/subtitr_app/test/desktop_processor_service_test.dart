import 'package:flutter_test/flutter_test.dart';
import 'package:subtitr_app/services/desktop_processor_service.dart';

void main() {
  test('DesktopVideo parses scan JSON', () {
    final video = DesktopVideo.fromJson({
      'name': 'movie.mp4',
      'path': r'E:\Subtitle\Kinolar\movie.mp4',
      'size': 1024,
      'subtitleName': 'movie.srt',
    });

    expect(video.name, 'movie.mp4');
    expect(video.size, 1024);
    expect(video.subtitleName, 'movie.srt');
  });
}
