import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Helm AI — Think Ahead",
  description: "Strategic Intelligence Operating System · AI Strategic Twin for Cities",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans text-white/90 antialiased">{children}</body>
    </html>
  );
}
