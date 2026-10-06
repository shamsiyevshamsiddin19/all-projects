import Link from "next/link";
import Image from "next/image";
import { auth } from "@/lib/auth";
import MobileNav from "@/components/MobileNav";
import NavLinks from "@/components/NavLinks";
import LangSelect from "@/components/LangSelect";
import ThemeToggle from "@/components/ThemeToggle";
import AccountMenu from "@/components/AccountMenu";
import AuthButton from "@/components/AuthButton";

export default async function Navbar() {
  let session = null;
  try {
    session = await auth();
  } catch {
    session = null;
  }

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-bg/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-4 sm:px-6">
        {/* Chap tomon: mobil menyu (chapda) + logo */}
        <div className="flex items-center gap-2">
          {/* Mobil menyu — chapda, logodan oldin */}
          <MobileNav />
          <Link href="/" className="flex items-center gap-2">
            <Image
              src="/logo-icon.png"
              alt="wstore.uz"
              width={36}
              height={36}
              priority
              className="h-9 w-9 object-contain"
            />
            <span className="text-lg font-semibold tracking-tight">
              wstore<span className="text-muted">.uz</span>
            </span>
          </Link>
        </div>

        {/* Markaziy menyu (desktop) */}
        <NavLinks />

        {/* O'ng: til + akkaunt */}
        <div className="flex items-center gap-3 sm:gap-4">
          <ThemeToggle />
          <LangSelect />
          {session?.user ? (
            <AccountMenu
              name={session.user.name}
              image={session.user.image}
              role={session.user.role}
            />
          ) : (
            <AuthButton />
          )}
        </div>
      </div>
    </header>
  );
}
