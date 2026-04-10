import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Auto Finance Atlas",
  description: "자동차 부품사 재무 리포트를 한눈에 보는 Django + Next.js 대시보드",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
