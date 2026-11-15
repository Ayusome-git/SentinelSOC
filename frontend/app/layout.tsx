import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppLayoutWrapper } from "@/components/layout/AppLayoutWrapper";

import { AuthProvider } from "@/lib/auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SentinelSOC",
  description: "AI-powered Security Operations Center",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#050505] text-zinc-50 overflow-hidden`}>
        <AuthProvider>
          <AppLayoutWrapper>
            {children}
          </AppLayoutWrapper>
        </AuthProvider>
      </body>
    </html>
  );
}
