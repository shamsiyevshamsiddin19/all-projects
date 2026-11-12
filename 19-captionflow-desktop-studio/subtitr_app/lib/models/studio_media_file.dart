import 'dart:io';
import 'package:flutter/material.dart';

/// Ilova studiyasida qo'llab-quvvatlanadigan fayl toifalari
enum StudioFileCategory {
  video,
  pdf,
  docx,
  markdown,
  subtitle,
  text,
  other,
}

/// Studiya pleyeri va hujjatlar o'quvchisida ko'rsatiladigan fayl modeli.
class StudioMediaFile {
  const StudioMediaFile({
    required this.path,
    required this.name,
    required this.displayName,
    required this.category,
    required this.extension,
  });

  final String path;
  final String name;
  final String displayName;
  final StudioFileCategory category;
  final String extension;

  bool get isVideo => category == StudioFileCategory.video;
  bool get isDocument => !isVideo;

  IconData get icon {
    switch (category) {
      case StudioFileCategory.video:
        return Icons.movie_outlined;
      case StudioFileCategory.pdf:
        return Icons.picture_as_pdf_outlined;
      case StudioFileCategory.docx:
        return Icons.description_outlined;
      case StudioFileCategory.markdown:
        return Icons.menu_book_rounded;
      case StudioFileCategory.subtitle:
        return Icons.subtitles_outlined;
      case StudioFileCategory.text:
      case StudioFileCategory.other:
        return Icons.article_outlined;
    }
  }

  Color get color {
    switch (category) {
      case StudioFileCategory.video:
        return const Color(0xFF10B981); // Emerald
      case StudioFileCategory.pdf:
        return const Color(0xFFEF4444); // Crimson
      case StudioFileCategory.docx:
        return const Color(0xFF3B82F6); // Blue
      case StudioFileCategory.markdown:
        return const Color(0xFFA855F7); // Purple
      case StudioFileCategory.subtitle:
        return const Color(0xFFF59E0B); // Amber
      case StudioFileCategory.text:
      case StudioFileCategory.other:
        return const Color(0xFF94A3B8); // Slate
    }
  }

  String get badgeText {
    final ext = extension.toUpperCase();
    if (ext.isNotEmpty) return ext;
    switch (category) {
      case StudioFileCategory.video:
        return 'VIDEO';
      case StudioFileCategory.pdf:
        return 'PDF';
      case StudioFileCategory.docx:
        return 'DOCX';
      case StudioFileCategory.markdown:
        return 'MD';
      case StudioFileCategory.subtitle:
        return 'SUB';
      case StudioFileCategory.text:
      case StudioFileCategory.other:
        return 'DOC';
    }
  }

  static StudioFileCategory categorize(String filePath) {
    final lower = filePath.toLowerCase();
    if (lower.endsWith('.mp4') ||
        lower.endsWith('.mkv') ||
        lower.endsWith('.webm') ||
        lower.endsWith('.avi') ||
        lower.endsWith('.mov') ||
        lower.endsWith('.m4v') ||
        lower.endsWith('.flv') ||
        lower.endsWith('.ts')) {
      return StudioFileCategory.video;
    }
    if (lower.endsWith('.pdf')) {
      return StudioFileCategory.pdf;
    }
    if (lower.endsWith('.docx') || lower.endsWith('.doc')) {
      return StudioFileCategory.docx;
    }
    if (lower.endsWith('.md')) {
      return StudioFileCategory.markdown;
    }
    if (lower.endsWith('.srt') ||
        lower.endsWith('.ass') ||
        lower.endsWith('.vtt')) {
      return StudioFileCategory.subtitle;
    }
    if (lower.endsWith('.txt') ||
        lower.endsWith('.json') ||
        lower.endsWith('.csv') ||
        lower.endsWith('.log')) {
      return StudioFileCategory.text;
    }
    return StudioFileCategory.other;
  }

  static bool isSupported(String filePath) {
    final lower = filePath.toLowerCase();
    const supported = [
      '.mp4',
      '.mkv',
      '.webm',
      '.avi',
      '.mov',
      '.m4v',
      '.flv',
      '.ts',
      '.pdf',
      '.docx',
      '.doc',
      '.md',
      '.txt',
      '.srt',
      '.ass',
      '.vtt',
      '.json',
      '.csv',
      '.log',
    ];
    return supported.any((ext) => lower.endsWith(ext));
  }

  static StudioMediaFile fromFile(File file) {
    final filename = file.uri.pathSegments.isNotEmpty
        ? file.uri.pathSegments.last
        : file.path;
    final dot = filename.lastIndexOf('.');
    final ext = dot >= 0 ? filename.substring(dot + 1) : '';
    final category = categorize(filename);

    String pretty = filename;
    final lower = filename.toLowerCase();
    if (lower.contains('oqish_tarjimali') && ext == 'pdf') {
      pretty = "Tarjimali konspekt (PDF)";
    } else if (lower.contains('oqish_alohida') && ext == 'pdf') {
      pretty = "Alohida konspekt (PDF)";
    } else if (lower.contains('oqish') && ext == 'pdf') {
      pretty = "O'qish konspekti (PDF)";
    } else if (lower.contains('oqish') && ext == 'md') {
      pretty = "O'qish materiali (Markdown)";
    } else if (lower.contains('oqish') && ext == 'txt') {
      pretty = "O'qish matni (TXT)";
    } else if (lower.contains('dual') && category == StudioFileCategory.video) {
      pretty = "Dual subtitrli video";
    } else if (lower.contains('original') || lower.contains('orig')) {
      pretty = category == StudioFileCategory.video
          ? "Asl video"
          : "Original subtitr ($ext)";
    } else if (category == StudioFileCategory.video) {
      pretty = "Video ($filename)";
    }

    return StudioMediaFile(
      path: file.path,
      name: filename,
      displayName: pretty,
      category: category,
      extension: ext,
    );
  }

  /// Berilgan fayl bilan bir papkada joylashgan barcha materiallarni topadi.
  static List<StudioMediaFile> discover(String initialPath) {
    final file = File(initialPath);
    final results = <StudioMediaFile>[];
    final seen = <String>{};

    void addFile(File f) {
      final p = f.path;
      if (seen.contains(p)) return;
      if (!isSupported(p)) return;
      seen.add(p);
      results.add(fromFile(f));
    }

    if (file.existsSync()) {
      addFile(file);
      final parent = file.parent;
      if (parent.existsSync()) {
        try {
          final entries = parent.listSync();
          for (final entity in entries) {
            if (entity is File) {
              addFile(entity);
            }
          }
        } catch (_) {}
      }
    } else {
      final dir = Directory(initialPath);
      if (dir.existsSync()) {
        try {
          final entries = dir.listSync();
          for (final entity in entries) {
            if (entity is File) {
              addFile(entity);
            }
          }
        } catch (_) {}
      }
    }

    // Saralash: Videolar, keyin PDF/DOCX/MD, keyin subtitrlar, keyin matnlar
    results.sort((a, b) {
      final priorityA = _categoryPriority(a.category);
      final priorityB = _categoryPriority(b.category);
      if (priorityA != priorityB) {
        return priorityA.compareTo(priorityB);
      }
      return a.name.compareTo(b.name);
    });

    return results;
  }

  static int _categoryPriority(StudioFileCategory c) {
    switch (c) {
      case StudioFileCategory.video:
        return 0;
      case StudioFileCategory.pdf:
        return 1;
      case StudioFileCategory.docx:
        return 2;
      case StudioFileCategory.markdown:
        return 3;
      case StudioFileCategory.subtitle:
        return 4;
      case StudioFileCategory.text:
        return 5;
      case StudioFileCategory.other:
        return 6;
    }
  }
}
