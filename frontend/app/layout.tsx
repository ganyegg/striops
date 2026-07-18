import type { Metadata } from "next";
import { DM_Sans, Space_Grotesk } from "next/font/google";
import ScrollToTop from "@/components/ScrollToTop";
import "./globals.css";

const sans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700"],
});

const display = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Striops — Trusted with foresight",
  description:
    "Strategic Intelligence Operating System — the strategic twin for cities. Trusted with foresight.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable}`}>
      <body className="font-sans text-white/90 antialiased">
        {children}
        <ScrollToTop />
      </body>
    </html>
  );
}
