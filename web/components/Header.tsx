import Link from "next/link";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 h-[60px] bg-ink border-b border-ink-soft shadow-[0_1px_0_rgba(208,74,2,0.35),0_4px_20px_rgba(0,0,0,0.25)]">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-[7px] bg-gradient-to-br from-flame to-tangerine text-xs font-bold text-white">
            AI
          </span>
          <span className="text-[14.5px] font-semibold tracking-tight text-white">
            Investment Engine
          </span>
        </Link>
        <nav className="flex items-center gap-2">
          <Link
            href="/diagnostic"
            className="rounded-full border border-[#2a2a2a] bg-[#161616] px-3 py-1 text-[10.5px] font-semibold uppercase tracking-wider text-[#b5b5b5] transition-colors hover:border-[#3e3e3e] hover:text-[#e0e0e0]"
          >
            New diagnostic
          </Link>
          <span className="rounded-full border border-flame/40 bg-[#161616] px-3 py-1 text-[10.5px] font-semibold uppercase tracking-wider text-tangerine">
            PwC Horizon
          </span>
        </nav>
      </div>
    </header>
  );
}
