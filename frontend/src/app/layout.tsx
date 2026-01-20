export const metadata = {
  title: 'CBC Chatbot PRO | Education Expert',
  description: "Your expert guide to Kenya's Competency-Based Curriculum (CBC) and Grade 10 transitions.",
}

import Navbar from "@/components/Navbar";
import ChatWidget from "@/components/ChatWidget";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[#0a0a0a]`}
      >
        <Navbar />
        <main className="pt-20 min-h-screen">
          {children}
        </main>
        <ChatWidget />
      </body>
    </html>
  );
}
