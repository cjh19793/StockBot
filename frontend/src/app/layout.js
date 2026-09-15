import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import NavShell from "@/components/NavShell";
import { AuthProvider } from "@/lib/authContext";

const sans = Inter({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", weight: ["400", "500", "700"] });

export const metadata = {
  title: "StockBot — 판단을 내려주는 주식 분석",
  description:
    "RSI · MACD · 볼린저밴드 · 스토캐스틱 · 몬테카를로 시뮬레이션을 조합해 매수/매도 신호를 계산하는 웹 기반 주식 분석 도구.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko" className={`${sans.variable} ${mono.variable}`}>
      <body className="min-h-screen bg-bg font-sans text-ink antialiased">
        <div className="fixed inset-0 z-0 bg-dot-grid opacity-[0.15]" />
        <div className="relative z-10 flex min-h-screen flex-col">
          <AuthProvider>
            <NavShell>{children}</NavShell>
          </AuthProvider>
        </div>
      </body>
    </html>
  );
}
