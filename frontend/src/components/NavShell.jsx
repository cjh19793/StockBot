"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/authContext";

const NAV_ITEMS = [
  { href: "/", label: "홈", icon: HomeIcon },
  { href: "/analyze", label: "종목분석", icon: ChartIcon },
  { href: "/compare", label: "종목비교", icon: CompareIcon },
  { href: "/montecarlo", label: "몬테카를로", icon: DiceIcon },
  { href: "/watchlist", label: "관심종목", icon: StarIcon },
];

function StarIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="m12 3 2.7 5.8 6.3.6-4.7 4.3 1.3 6.2-5.6-3.2-5.6 3.2 1.3-6.2-4.7-4.3 6.3-.6z" />
    </svg>
  );
}

function HomeIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9" />
    </svg>
  );
}
function ChartIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M3 3v18h18" />
      <path d="m7 15 4-5 3 3 5-7" />
    </svg>
  );
}
function CompareIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="10" width="6" height="11" />
      <rect x="10" y="5" width="6" height="16" />
      <rect x="17" y="13" width="4" height="8" />
    </svg>
  );
}
function DiceIcon(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <circle cx="8.5" cy="8.5" r="1.25" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="8.5" r="1.25" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.25" fill="currentColor" stroke="none" />
      <circle cx="8.5" cy="15.5" r="1.25" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="15.5" r="1.25" fill="currentColor" stroke="none" />
    </svg>
  );
}

function AuthControl() {
  const { user, loading, signOut } = useAuth();

  if (loading) return null;

  if (!user) {
    return (
      <Link
        href="/login"
        className="rounded-md bg-amber px-4 py-2 text-[13.5px] font-semibold text-[#1A1000] transition-opacity hover:opacity-90"
      >
        로그인
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <span className="hidden max-w-[160px] truncate text-[13px] text-ink-dim sm:inline">{user.email}</span>
      <button
        type="button"
        onClick={signOut}
        className="rounded-md border border-border px-3.5 py-2 text-[13px] text-ink-dim transition-colors hover:text-ink"
      >
        로그아웃
      </button>
    </div>
  );
}

export default function NavShell({ children }) {
  const pathname = usePathname();

  return (
    <>
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
            <span className="flex h-6 w-6 items-center justify-center rounded border border-amber font-mono text-[11px] font-bold text-amber">
              S
            </span>
            StockBot
          </Link>
          <nav className="hidden items-center gap-8 text-sm text-ink-dim sm:flex">
            {NAV_ITEMS.slice(1).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`transition-colors hover:text-ink ${
                  pathname === item.href ? "text-amber" : ""
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <AuthControl />
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 pb-24 pt-8 sm:px-8 sm:pb-12">{children}</main>

      <footer className="hidden border-t border-border py-6 sm:block">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 text-[12.5px] font-mono text-ink-faint sm:px-8">
          <span className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 items-center justify-center rounded border border-amber text-[9px] font-bold text-amber">
              S
            </span>
            StockBot
          </span>
          <span>투자 판단의 참고 자료이며, 투자 권유가 아닙니다.</span>
        </div>
      </footer>

      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-border bg-bg-raised/95 backdrop-blur sm:hidden">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] ${
                active ? "text-amber" : "text-ink-faint"
              }`}
            >
              <Icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
