import 'package:flutter/material.dart';

enum SidebarView { video, settings, results }

class AppSidebar extends StatelessWidget {
  const AppSidebar({
    super.key,
    required this.currentMode,
    required this.currentView,
    required this.isRunning,
    required this.hasResults,
    required this.onModeChanged,
    required this.onViewChanged,
    this.progress = 0,
  });

  final String currentMode;
  final SidebarView currentView;
  final bool isRunning;
  final bool hasResults;
  final ValueChanged<String> onModeChanged;
  final ValueChanged<SidebarView> onViewChanged;
  final double progress;

  static const hardsubModes = {
    'dual_vocab',
    'original_vocab',
    'dual',
    'original',
    'translated',
  };
  static const softsubModes = {
    'softsub',
    'softsub_dual',
    'softsub_translated',
    'softsub_original',
  };
  static const _videoModes = {
    ...hardsubModes,
    ...softsubModes,
    'dubbing',
  };

  @override
  Widget build(BuildContext context) {
    final isHardsub = hardsubModes.contains(currentMode) ||
        (!_videoModes.contains(currentMode) &&
            !softsubModes.contains(currentMode) &&
            currentMode != 'dubbing');
    final isSoftsub = softsubModes.contains(currentMode);
    final isDubbing = currentMode == 'dubbing';

    return Container(
      width: 68,
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A0A),
        border: Border(
          right: BorderSide(color: Color(0xFF1A1A1A)),
        ),
      ),
      child: Column(
        children: [
          const SizedBox(height: 16),
          _SidebarModeButton(
            icon: Icons.movie_filter_rounded,
            label: 'Kuydirish',
            isSelected: isHardsub,
            activeColor: const Color(0xFF2563EB),
            enabled: !isRunning,
            onTap: () {
              onModeChanged(
                hardsubModes.contains(currentMode)
                    ? currentMode
                    : 'dual_vocab',
              );
              onViewChanged(SidebarView.video);
            },
          ),
          const SizedBox(height: 6),
          _SidebarModeButton(
            icon: Icons.closed_caption_rounded,
            label: 'Yumshoq',
            isSelected: isSoftsub,
            activeColor: const Color(0xFF0284C7),
            enabled: !isRunning,
            onTap: () {
              onModeChanged(
                softsubModes.contains(currentMode)
                    ? currentMode
                    : 'softsub',
              );
              onViewChanged(SidebarView.video);
            },
          ),
          const SizedBox(height: 6),
          _SidebarModeButton(
            icon: Icons.record_voice_over_rounded,
            label: 'Dublyaj',
            isSelected: isDubbing,
            activeColor: const Color(0xFF7C3AED),
            enabled: !isRunning,
            onTap: () {
              onModeChanged('dubbing');
              onViewChanged(SidebarView.video);
            },
          ),
          const SizedBox(height: 12),
          Container(
            width: 36,
            height: 1,
            color: const Color(0xFF262626),
          ),
          const SizedBox(height: 12),
          _SidebarNavButton(
            icon: Icons.video_library_outlined,
            label: 'Video',
            isSelected: currentView == SidebarView.video,
            onTap: () => onViewChanged(SidebarView.video),
          ),
          const SizedBox(height: 4),
          _SidebarNavButton(
            icon: Icons.tune_rounded,
            label: 'Sozlama',
            isSelected: currentView == SidebarView.settings,
            onTap: () => onViewChanged(SidebarView.settings),
          ),
          const SizedBox(height: 4),
          _SidebarNavButton(
            icon: Icons.assessment_outlined,
            label: 'Natija',
            isSelected: currentView == SidebarView.results,
            badge: hasResults,
            onTap: () => onViewChanged(SidebarView.results),
          ),
          const Spacer(),
          if (isRunning)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: SizedBox(
                width: 28,
                height: 28,
                child: CircularProgressIndicator(
                  value: progress > 0.01 ? progress : null,
                  strokeWidth: 2.5,
                  color: const Color(0xFF2563EB),
                  backgroundColor: const Color(0xFF222222),
                ),
              ),
            ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _SidebarModeButton extends StatelessWidget {
  const _SidebarModeButton({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.activeColor,
    required this.enabled,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final bool isSelected;
  final Color activeColor;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Tooltip(
        message: label,
        preferBelow: false,
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: enabled ? onTap : null,
            borderRadius: BorderRadius.circular(10),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: isSelected
                    ? activeColor.withValues(alpha: 0.18)
                    : Colors.transparent,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: isSelected ? activeColor : Colors.transparent,
                  width: 1.5,
                ),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    icon,
                    size: 20,
                    color: isSelected
                        ? activeColor
                        : const Color(0xFF71717A),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    label,
                    style: TextStyle(
                      fontSize: 8.5,
                      fontWeight: isSelected
                          ? FontWeight.w600
                          : FontWeight.w400,
                      color: isSelected
                          ? activeColor
                          : const Color(0xFF71717A),
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

class _SidebarNavButton extends StatelessWidget {
  const _SidebarNavButton({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
    this.badge = false,
  });

  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final bool badge;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            width: 52,
            height: 44,
            decoration: BoxDecoration(
              color: isSelected
                  ? const Color(0xFF1A1A1A)
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Badge(
                  isLabelVisible: badge,
                  smallSize: 7,
                  backgroundColor: const Color(0xFF22C55E),
                  child: Icon(
                    icon,
                    size: 18,
                    color: isSelected
                        ? Colors.white
                        : const Color(0xFF71717A),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 8.5,
                    fontWeight:
                        isSelected ? FontWeight.w500 : FontWeight.w400,
                    color: isSelected
                        ? Colors.white
                        : const Color(0xFF71717A),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
