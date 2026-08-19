import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/settings_store.dart';

/// Screen where the user enters their own AI provider API keys. Nothing is
/// bundled with the app; each user pastes their own keys here.
class ApiKeysScreen extends StatefulWidget {
  const ApiKeysScreen({super.key, required this.initial});

  final AppSettings initial;

  @override
  State<ApiKeysScreen> createState() => _ApiKeysScreenState();
}

class _ApiKeysScreenState extends State<ApiKeysScreen> {
  final SettingsStore _store = SettingsStore();

  late final TextEditingController _groq;
  late final TextEditingController _openai;
  late final TextEditingController _gemini;
  late final TextEditingController _anthropic;
  late final TextEditingController _groqModel;
  late final TextEditingController _openaiModel;
  late final TextEditingController _geminiModel;
  late final TextEditingController _anthropicModel;

  bool _obscure = true;
  bool _advanced = false;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _groq = TextEditingController(text: widget.initial.groqApiKey);
    _openai = TextEditingController(text: widget.initial.openaiApiKey);
    _gemini = TextEditingController(text: widget.initial.geminiApiKey);
    _anthropic = TextEditingController(text: widget.initial.anthropicApiKey);
    _groqModel = TextEditingController(text: widget.initial.groqWhisperModel);
    _openaiModel = TextEditingController(text: widget.initial.openaiModel);
    _geminiModel = TextEditingController(text: widget.initial.geminiModel);
    _anthropicModel = TextEditingController(text: widget.initial.anthropicModel);
    _advanced = widget.initial.groqWhisperModel.isNotEmpty ||
        widget.initial.openaiModel.isNotEmpty ||
        widget.initial.geminiModel.isNotEmpty ||
        widget.initial.anthropicModel.isNotEmpty;
  }

  @override
  void dispose() {
    _groq.dispose();
    _openai.dispose();
    _gemini.dispose();
    _anthropic.dispose();
    _groqModel.dispose();
    _openaiModel.dispose();
    _geminiModel.dispose();
    _anthropicModel.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    final settings = AppSettings(
      groqApiKey: _groq.text,
      openaiApiKey: _openai.text,
      geminiApiKey: _gemini.text,
      anthropicApiKey: _anthropic.text,
      groqWhisperModel: _groqModel.text,
      openaiModel: _openaiModel.text,
      geminiModel: _geminiModel.text,
      anthropicModel: _anthropicModel.text,
    );
    await _store.save(settings);
    if (!mounted) return;
    setState(() => _saving = false);
    Navigator.of(context).pop(settings);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('API kalitlar'),
        titleTextStyle: theme.textTheme.titleLarge?.copyWith(
          fontWeight: FontWeight.w800,
          letterSpacing: -0.5,
        ),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                _InfoBanner(theme: theme),
                const SizedBox(height: 24),
                _KeyField(
                  controller: _groq,
                  label: 'Groq API kalit',
                  hint: 'gsk_...',
                  helper: 'Nutqni matnga aylantirish (Whisper) va tarjima. console.groq.com',
                  obscure: _obscure,
                ),
                const SizedBox(height: 20),
                _KeyField(
                  controller: _openai,
                  label: 'OpenAI API kalit',
                  hint: 'sk-...',
                  helper: 'Eng sifatli tarjima uchun. platform.openai.com',
                  obscure: _obscure,
                ),
                const SizedBox(height: 20),
                _KeyField(
                  controller: _gemini,
                  label: 'Gemini API kalit',
                  hint: 'AI...',
                  helper: 'Google tarjima muqobili. aistudio.google.com',
                  obscure: _obscure,
                ),
                const SizedBox(height: 20),
                _KeyField(
                  controller: _anthropic,
                  label: 'Claude (Anthropic) API kalit',
                  hint: 'sk-ant-...',
                  helper: 'Yuqori sifatli tarjima. console.anthropic.com',
                  obscure: _obscure,
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Switch(
                      value: !_obscure,
                      onChanged: (v) => setState(() => _obscure = !v),
                    ),
                    const Text('Kalitlarni ko\'rsatish'),
                  ],
                ),
                const Divider(height: 32),
                _AdvancedSection(
                  expanded: _advanced,
                  onToggle: () => setState(() => _advanced = !_advanced),
                  groqModel: _groqModel,
                  openaiModel: _openaiModel,
                  geminiModel: _geminiModel,
                  anthropicModel: _anthropicModel,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _saving ? null : _save,
                  icon: _saving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.save_rounded),
                  label: const Text('Saqlash'),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  'Kalitlar faqat shu kompyuterda saqlanadi. Agar hech qanday '
                  'kalit kiritmasangiz, dastur cheklangan oflayn lug\'at bilan '
                  'ishlaydi.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
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

class _InfoBanner extends StatelessWidget {
  const _InfoBanner({required this.theme});
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: theme.colorScheme.outline),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.key_rounded, color: theme.colorScheme.primary),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Dastur ishlashi uchun o\'zingizning API kalitingizni kiriting. '
              'Kamida bittasini kiritish tavsiya etiladi — Groq bepul beriladi.',
              style: theme.textTheme.bodyMedium,
            ),
          ),
        ],
      ),
    );
  }
}

class _KeyField extends StatelessWidget {
  const _KeyField({
    required this.controller,
    required this.label,
    required this.hint,
    required this.helper,
    required this.obscure,
  });

  final TextEditingController controller;
  final String label;
  final String hint;
  final String helper;
  final bool obscure;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      obscuringCharacter: '•',
      autocorrect: false,
      enableSuggestions: false,
      inputFormatters: [FilteringTextInputFormatter.deny(RegExp(r'\s'))],
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        helperText: helper,
        helperMaxLines: 2,
        prefixIcon: const Icon(Icons.vpn_key_outlined),
      ),
    );
  }
}

class _AdvancedSection extends StatelessWidget {
  const _AdvancedSection({
    required this.expanded,
    required this.onToggle,
    required this.groqModel,
    required this.openaiModel,
    required this.geminiModel,
    required this.anthropicModel,
  });

  final bool expanded;
  final VoidCallback onToggle;
  final TextEditingController groqModel;
  final TextEditingController openaiModel;
  final TextEditingController geminiModel;
  final TextEditingController anthropicModel;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: onToggle,
          borderRadius: BorderRadius.circular(8),
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              children: [
                Icon(expanded ? Icons.expand_less : Icons.expand_more),
                const SizedBox(width: 8),
                const Text('Qo\'shimcha: model sozlamalari (ixtiyoriy)'),
              ],
            ),
          ),
        ),
        if (expanded) ...[
          const SizedBox(height: 12),
          _ModelField(controller: groqModel, label: 'Groq Whisper modeli', hint: 'whisper-large-v3'),
          const SizedBox(height: 16),
          _ModelField(controller: openaiModel, label: 'OpenAI modeli', hint: 'gpt-4o-mini'),
          const SizedBox(height: 16),
          _ModelField(controller: geminiModel, label: 'Gemini modeli', hint: 'gemini-2.5-flash'),
          const SizedBox(height: 16),
          _ModelField(controller: anthropicModel, label: 'Claude modeli', hint: 'claude-sonnet-5'),
        ],
      ],
    );
  }
}

class _ModelField extends StatelessWidget {
  const _ModelField({required this.controller, required this.label, required this.hint});
  final TextEditingController controller;
  final String label;
  final String hint;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      autocorrect: false,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: const Icon(Icons.tune_rounded),
      ),
    );
  }
}
