import Link from "next/link";
import { signIn } from "@/lib/auth";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-sm rounded-card border border-border bg-surface p-8 text-center">
        <Link href="/" className="mb-6 inline-flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-border-strong bg-bg text-lg font-bold text-accent">
            W
          </span>
          <span className="text-xl font-semibold">
            wstore<span className="text-muted">.uz</span>
          </span>
        </Link>

        <h1 className="mb-1 text-lg font-semibold text-fg">
          Akkauntga kirish
        </h1>
        <p className="mb-6 text-sm text-muted">
          Google orqali kirasiz — ro'yxatdan o'tish avtomatik bo'ladi.
        </p>

        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/" });
          }}
        >
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-white py-2.5 text-sm font-medium text-black transition hover:bg-gray-100">
            <GoogleIcon />
            Google bilan davom etish
          </button>
        </form>

        <p className="mt-6 text-xs text-muted">
          Kirish orqali siz foydalanish shartlariga rozilik bildirasiz.
        </p>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden>
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3C33.7 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6.1 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6.1 29.6 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.3 0-9.7-3.1-11.3-7.6l-6.5 5C9.5 39.6 16.2 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.1-4.1 5.5l6.2 5.2C41.9 35.6 44 30.2 44 24c0-1.3-.1-2.3-.4-3.5z"
      />
    </svg>
  );
}
