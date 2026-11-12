import 'package:flutter/material.dart';

/// Home sahifasining barqaror yuqori paneli.
///
/// U ekranning ish holatini saqlamaydi: barcha amallar callback orqali
/// beriladi. Shu sabab job holati o'zgarganda UI va lifecycle bir faylga
/// bog'lanib qolmaydi.
class HomeScreenAppBar extends StatelessWidget implements PreferredSizeWidget {
  const HomeScreenAppBar({
    super.key,
    required this.appVersion,
    required this.hasApiKey,
    required this.configuredProviders,
    required this.isRunning,
    required this.unreadNotificationCount,
    required this.canOpenOutput,
    required this.onOpenApiKeys,
    required this.onInstallDependencies,
    required this.onShowNotifications,
    required this.onOpenOutput,
  });

  final String? appVersion;
  final bool hasApiKey;
  final List<String> configuredProviders;
  final bool isRunning;
  final int unreadNotificationCount;
  final bool canOpenOutput;
  final VoidCallback onOpenApiKeys;
  final VoidCallback onInstallDependencies;
  final VoidCallback onShowNotifications;
  final VoidCallback onOpenOutput;

  @override
  Size get preferredSize => const Size.fromHeight(70);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final actionStyle = IconButton.styleFrom(
      backgroundColor: theme.colorScheme.surfaceContainerHighest,
    );
    return AppBar(
      titleSpacing: 24,
      toolbarHeight: 70,
      title: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.asset(
              'assets/app_logo.png',
              width: 36,
              height: 36,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(width: 16),
          Text(
            'Subtitr Desktop',
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w800,
              letterSpacing: -0.5,
            ),
          ),
          if (appVersion != null) ...[
            const SizedBox(width: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                'v$appVersion',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ],
      ),
      actions: [
        IconButton(
          tooltip: hasApiKey
              ? 'API kalitlar (${configuredProviders.join(", ")})'
              : 'API kalitlarni kiriting',
          onPressed: isRunning ? null : onOpenApiKeys,
          icon: Badge(
            isLabelVisible: !hasApiKey,
            backgroundColor: Colors.amber,
            child: const Icon(Icons.key_rounded),
          ),
          style: actionStyle,
        ),
        const SizedBox(width: 8),
        IconButton(
          tooltip: 'Paketlarni o\'rnatish',
          onPressed: isRunning ? null : onInstallDependencies,
          icon: const Icon(Icons.download_for_offline_rounded),
          style: actionStyle,
        ),
        const SizedBox(width: 8),
        IconButton(
          tooltip: 'Bildirishnomalar',
          onPressed: onShowNotifications,
          icon: Badge(
            isLabelVisible: unreadNotificationCount > 0,
            label: Text('$unreadNotificationCount'),
            child: const Icon(Icons.notifications_none_rounded),
          ),
          style: actionStyle,
        ),
        const SizedBox(width: 8),
        IconButton(
          tooltip: 'Tayyor natijalar papkasini ochish',
          onPressed: canOpenOutput ? onOpenOutput : null,
          icon: const Icon(Icons.output_rounded),
          style: actionStyle,
        ),
        const SizedBox(width: 24),
      ],
    );
  }
}

/// Drag-and-drop paytida foydalanuvchiga ko'rinadigan qabul qiluvchi qatlam.
class HomeDropOverlay extends StatelessWidget {
  const HomeDropOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Positioned.fill(
      child: IgnorePointer(
        child: Container(
          color: Colors.black.withValues(alpha: 0.78),
          child: Center(
            child: Container(
              margin: const EdgeInsets.all(32),
              padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 36),
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: theme.colorScheme.primary,
                  width: 2.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: theme.colorScheme.primary.withValues(alpha: 0.25),
                    blurRadius: 32,
                    spreadRadius: 6,
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.file_download_outlined,
                    size: 64,
                    color: theme.colorScheme.primary,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Video, papka yoki subtitr faylini tashlang',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: theme.colorScheme.onSurface,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'MP4, MKV, AVI, MOV, SRT, VTT yoki butun boshli papka',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
