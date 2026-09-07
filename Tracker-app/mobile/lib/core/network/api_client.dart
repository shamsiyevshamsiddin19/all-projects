import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/api_constants.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;

  late Dio dio;
  String? _accessToken;
  String? _refreshToken;

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.defaultBaseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          if (_accessToken != null) {
            options.headers["Authorization"] = "Bearer $_accessToken";
          }
          return handler.next(options);
        },
        onError: (DioException error, handler) async {
          // If 401 and refresh token exists, try refreshing once
          if (error.response?.statusCode == 401 && _refreshToken != null) {
            try {
              final refreshDio = Dio(BaseOptions(baseUrl: dio.options.baseUrl));
              final res = await refreshDio.post(
                ApiConstants.authRefresh,
                data: {"refresh_token": _refreshToken},
              );
              if (res.statusCode == 200) {
                final newAccess = res.data["access_token"];
                final newRefresh = res.data["refresh_token"];
                await saveTokens(newAccess, newRefresh);

                // Retry original request
                error.requestOptions.headers["Authorization"] = "Bearer $newAccess";
                final clonedResponse = await dio.fetch(error.requestOptions);
                return handler.resolve(clonedResponse);
              }
            } catch (_) {
              await clearTokens();
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString("access_token");
    _refreshToken = prefs.getString("refresh_token");
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString("access_token", accessToken);
    await prefs.setString("refresh_token", refreshToken);
  }

  Future<void> clearTokens() async {
    _accessToken = null;
    _refreshToken = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove("access_token");
    await prefs.remove("refresh_token");
    await prefs.remove("cached_user");
  }

  String getErrorMessage(dynamic error) {
    if (error is DioException) {
      if (error.response?.data != null && error.response?.data["detail"] != null) {
        return error.response?.data["detail"].toString() ?? "Xatolik yuz berdi";
      }
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout) {
        return "Server bilan aloqa vaqti tugadi. Internetni tekshiring.";
      }
      if (error.type == DioExceptionType.connectionError) {
        return "Serverga ulanib bo'lmadi. Server ishlab turganini tekshiring.";
      }
    }
    return error.toString();
  }
}
