import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_colors.dart';
import '../../shared/widgets/custom_button.dart';
import '../../shared/widgets/custom_text_field.dart';
import '../groups/group_provider.dart';
import 'assignment_provider.dart';

class CreateAssignmentScreen extends StatefulWidget {
  const CreateAssignmentScreen({super.key});

  @override
  State<CreateAssignmentScreen> createState() => _CreateAssignmentScreenState();
}

class _CreateAssignmentScreenState extends State<CreateAssignmentScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  final _instructController = TextEditingController();
  final _maxScoreController = TextEditingController(text: "100");

  String? _selectedGroupId;
  DateTime _selectedDeadline = DateTime.now().add(const Duration(days: 3));
  TimeOfDay _selectedTime = const TimeOfDay(hour: 23, minute: 59);
  String _selectedPriority = "MEDIUM";

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<GroupProvider>().fetchGroups();
    });
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _instructController.dispose();
    _maxScoreController.dispose();
    super.dispose();
  }

  Future<void> _pickDeadline() async {
    final pickedDate = await showDatePicker(
      context: context,
      initialDate: _selectedDeadline,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (pickedDate == null) return;

    if (!mounted) return;
    final pickedTime = await showTimePicker(
      context: context,
      initialTime: _selectedTime,
    );
    if (pickedTime == null) return;

    setState(() {
      _selectedDeadline = pickedDate;
      _selectedTime = pickedTime;
    });
  }

  void _onCreate() async {
    if (!_formKey.currentState!.validate()) return;

    final finalDeadline = DateTime(
      _selectedDeadline.year,
      _selectedDeadline.month,
      _selectedDeadline.day,
      _selectedTime.hour,
      _selectedTime.minute,
    );

    final score = int.tryParse(_maxScoreController.text) ?? 100;

    final assignProv = context.read<AssignmentProvider>();
    final ok = await assignProv.createAssignment(
      title: _titleController.text.trim(),
      description: _descController.text.trim(),
      instructions: _instructController.text.trim().isNotEmpty ? _instructController.text.trim() : null,
      groupId: _selectedGroupId,
      deadline: finalDeadline,
      priority: _selectedPriority,
      maxScore: score,
    );

    if (!mounted) return;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Vazifa muvaffaqiyatli chop etildi! 🚀"),
          backgroundColor: AppColors.success,
        ),
      );
      Navigator.of(context).pop();
    } else if (assignProv.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(assignProv.errorMessage!),
          backgroundColor: AppColors.danger,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final groupProv = context.watch<GroupProvider>();
    final assignProv = context.watch<AssignmentProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final deadlineString = DateFormat("d MMMM yyyy, HH:mm").format(
      DateTime(
        _selectedDeadline.year,
        _selectedDeadline.month,
        _selectedDeadline.day,
        _selectedTime.hour,
        _selectedTime.minute,
      ),
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text("Yangi Vazifa Yaratish"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CustomTextField(
                label: "Vazifa sarlavhasi",
                hint: "Masalan: Database Modellari va Migratsiyalar",
                controller: _titleController,
                validator: (v) => (v == null || v.trim().length < 3) ? "Sarlavha kiriting" : null,
              ),
              const SizedBox(height: 16),
              CustomTextField(
                label: "Tavsif",
                hint: "Vazifa shartlari haqida qisqacha ma'lumot",
                controller: _descController,
                maxLines: 3,
                validator: (v) => (v == null || v.trim().length < 3) ? "Tavsif kiriting" : null,
              ),
              const SizedBox(height: 16),
              CustomTextField(
                label: "Bajarish yo'riqnomasi (ixtiyoriy)",
                hint: "Qadamlar, qoidalar, fayllarni yuborish tartibi",
                controller: _instructController,
                maxLines: 3,
              ),
              const SizedBox(height: 16),

              // Group Selector Dropdown
              const Text("Guruhni tanlang", style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                initialValue: _selectedGroupId,
                decoration: InputDecoration(
                  hintText: "Barcha guruhlar yoki aniq birini tanlang",
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
                items: [
                  const DropdownMenuItem(value: null, child: Text("Guruhsiz (Umumiy)")),
                  ...groupProv.groups.map((g) => DropdownMenuItem(value: g.id, child: Text(g.name))),
                ],
                onChanged: (val) => setState(() => _selectedGroupId = val),
              ),
              const SizedBox(height: 16),

              // Deadline Picker
              const Text("Topshirish muddati (Deadline)", style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: _pickDeadline,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    color: isDark ? AppColors.darkSurface : AppColors.lightSurface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.calendar_month_rounded, size: 20, color: AppColors.primary),
                          const SizedBox(width: 10),
                          Text(deadlineString, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                        ],
                      ),
                      const Icon(Icons.edit_calendar_rounded, size: 18, color: Colors.grey),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Priority & Max Score
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("Ustuvorlik", style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 6),
                        DropdownButtonFormField<String>(
                          initialValue: _selectedPriority,
                          decoration: InputDecoration(
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                          items: const [
                            DropdownMenuItem(value: "LOW", child: Text("Past")),
                            DropdownMenuItem(value: "MEDIUM", child: Text("O'rtacha")),
                            DropdownMenuItem(value: "HIGH", child: Text("Yuqori")),
                            DropdownMenuItem(value: "URGENT", child: Text("Shoshilinch")),
                          ],
                          onChanged: (val) {
                            if (val != null) setState(() => _selectedPriority = val);
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: CustomTextField(
                      label: "Maksimal ball",
                      hint: "100",
                      controller: _maxScoreController,
                      keyboardType: TextInputType.number,
                      validator: (v) {
                        final val = int.tryParse(v ?? "");
                        if (val == null || val <= 0) return "Noto'g'ri ball";
                        return null;
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              CustomButton(
                text: "Vazifani E'lon Qilish",
                onPressed: _onCreate,
                isLoading: assignProv.isLoading,
                icon: Icons.send_rounded,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
