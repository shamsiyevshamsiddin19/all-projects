import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';

class UserModel {
  final String id;
  final String email;
  final String fullName;
  final String role; // "TEACHER" or "STUDENT"
  final String? avatarUrl;
  final String? phone;

  UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    this.avatarUrl,
    this.phone,
  });

  bool get isTeacher => role.toUpperCase() == "TEACHER";
  bool get isStudent => role.toUpperCase() == "STUDENT";

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json["id"] ?? "",
      email: json["email"] ?? "",
      fullName: json["full_name"] ?? "",
      role: json["role"] ?? "STUDENT",
      avatarUrl: json["avatar_url"],
      phone: json["phone"],
    );
  }

  Map<String, dynamic> toJson() => {
    "id": id,
    "email": email,
    "full_name": fullName,
    "role": role,
    "avatar_url": avatarUrl,
    "phone": phone,
  };
}

class AuthProvider extends ChangeNotifier {
  final ApiClient _api = ApiClient();
  UserModel? _user;
  bool _isLoading = false;
  String? _errorMessage;
  ThemeMode _themeMode = ThemeMode.dark;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _user != null;
  ThemeMode get themeMode => _themeMode;
  bool get isDarkMode => _themeMode == ThemeMode.dark;

  void toggleTheme() {
    _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    notifyListeners();
  }

  Future<void> initAuth() async {
    _isLoading = true;
    notifyListeners();
    try {
      await _api.init();
      final prefs = await SharedPreferences.getInstance();
      final userJson = prefs.getString("cached_user");
      if (userJson != null) {
        _user = UserModel.fromJson(jsonDecode(userJson));
      }

      // Refresh profile from backend
      if (_user != null) {
        final res = await _api.dio.get(ApiConstants.authMe);
        if (res.statusCode == 200) {
          _user = UserModel.fromJson(res.data);
          await prefs.setString("cached_user", jsonEncode(_user!.toJson()));
        }
      }
    } catch (_) {
      // keep cached user if offline
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        ApiConstants.authLogin,
        data: {
          "email": email.trim(),
          "password": password,
        },
      );

      if (res.statusCode == 200) {
        final access = res.data["access_token"];
        final refresh = res.data["refresh_token"];
        _user = UserModel.fromJson(res.data["user"]);

        await _api.saveTokens(access, refresh);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString("cached_user", jsonEncode(_user!.toJson()));

        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> register({
    required String email,
    required String password,
    required String fullName,
    required String role,
    String? phone,
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _api.dio.post(
        ApiConstants.authRegister,
        data: {
          "email": email.trim(),
          "password": password,
          "full_name": fullName.trim(),
          "role": role,
          "phone": phone?.trim(),
        },
      );

      if (res.statusCode == 201) {
        final access = res.data["access_token"];
        final refresh = res.data["refresh_token"];
        _user = UserModel.fromJson(res.data["user"]);

        await _api.saveTokens(access, refresh);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString("cached_user", jsonEncode(_user!.toJson()));

        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      _errorMessage = _api.getErrorMessage(e);
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await _api.clearTokens();
    _user = null;
    notifyListeners();
  }
}
