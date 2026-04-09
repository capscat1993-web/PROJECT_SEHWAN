"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function HomeIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M5 9.2h3V19H5V9.2zM10.6 5h2.8v14h-2.8V5zm5.6 8H19v6h-2.8v-6z" />
    </svg>
  );
}

function LogoIcon() {
  return (
    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
      <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
    </svg>
  );
}

function NavItem({
  href,
  active,
  label,
  children,
}: {
  href: string;
  active: boolean;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`group relative flex items-center justify-center w-12 h-12 rounded-2xl transition-all ${
        active
          ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/30"
          : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
      }`}
    >
      {children}
      <span className="absolute left-14 bg-slate-900 text-white text-[10px] px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
        {label}
      </span>
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const isHome = pathname === "/";
  const isDetail = pathname.startsWith("/company");

  return (
    <aside className="fixed left-4 top-4 bottom-4 w-20 bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl z-50 flex flex-col items-center py-8 border-4 border-white">
      <div className="w-12 h-12 bg-indigo-500 rounded-2xl flex items-center justify-center mb-10 shadow-lg shadow-indigo-500/30">
        <LogoIcon />
      </div>
      <nav className="flex flex-col gap-6">
        <NavItem href="/" active={isHome} label="기업 목록">
          <HomeIcon />
        </NavItem>
        <NavItem href="/" active={isDetail} label="재무 분석">
          <ChartIcon />
        </NavItem>
      </nav>
    </aside>
  );
}
