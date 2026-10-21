/**
 * Foldex Autentifikatsiya va Sessiya Boshqaruv Skripti (auth.js)
 * Telegram WebApp va bir martalik tokenlar orqali xavfsiz API so'rovlarni ta'minlaydi.
 */

const Auth = {
    // 1. Tizimga kirish holatini tekshirish
    async checkAuth() {
        // a) Agar URL da ?token= bo'lsa (Botdan /login havolasi orqali kelingan bo'lsa)
        const urlParams = new URLSearchParams(window.location.search);
        const urlToken = urlParams.get("token");

        if (urlToken) {
            try {
                const resp = await fetch("/api/auth/verify-token", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token: urlToken })
                });
                if (resp.ok) {
                    // Token muvaffaqiyatli qabul qilindi, URL ni tozalaymiz
                    window.history.replaceState({}, document.title, window.location.pathname);
                    return true;
                }
            } catch (e) {
                console.error("Token verification failed:", e);
            }
        }

        // b) Agar Telegram Mini App (WebApp) ichida ochilgan bo'lsa
        if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
            try {
                const resp = await fetch("/api/auth/webapp", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ init_data: window.Telegram.WebApp.initData })
                });
                if (resp.ok) {
                    return true;
                }
            } catch (e) {
                console.error("WebApp auth failed:", e);
            }
        }

        // c) Cookie sessiyasini /api/auth/me orqali tekshirish
        try {
            const meResp = await fetch("/api/auth/me");
            if (meResp.ok) {
                return true;
            }
        } catch (e) {
            console.error("Session check failed:", e);
        }

        // Agar hech qanday autentifikatsiya bo'lmasa — /login sahifasiga yo'naltirish
        window.location.href = "/login";
        return false;
    },

    // 2. Tizimdan chiqish (Logout)
    async logout() {
        try {
            await fetch("/api/auth/logout", { method: "POST" });
        } catch (e) {}
        window.location.href = "/login";
    }
};

// Global doiraga chiqarish
window.Auth = Auth;
