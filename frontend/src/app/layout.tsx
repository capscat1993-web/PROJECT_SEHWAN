import type { Metadata } from "next";
import { Bungee, Noto_Sans_KR } from "next/font/google";
import { Sidebar } from "@/components/sidebar";
import "./globals.css";

const bungee = Bungee({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-bungee",
  display: "swap",
});

const notoSansKR = Noto_Sans_KR({
  weight: ["400", "500", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-noto",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: "기업 재무 리포트",
  description: "국내 기업의 재무 건전성 분석 플랫폼",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className={`${bungee.variable} ${notoSansKR.variable}`}>
      <body>
        <Sidebar />
        {children}
      </body>
    </html>
  );
}
