"use client";

import React, { useState } from "react";
import Link from "next/link";
import { GraduationCap, Menu, X, BookOpen, Users, Phone } from "lucide-react";
import { usePathname } from "next/navigation";

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const pathname = usePathname();

    const navLinks = [
        { name: "Home", href: "/" },
        { name: "Pathways", href: "/pathways" },
        { name: "Knowledge Base", href: "/knowledge" }, // Kept for admin/demo purposes
        { name: "About", href: "/about" },
    ];

    const isActive = (path: string) => pathname === path;

    return (
        <nav className="fixed top-0 left-0 w-full z-50 bg-black/50 backdrop-blur-lg border-b border-white/10">
            <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-3 group">
                    <div className="p-2 bg-gradient-to-br from-red-600 to-red-800 rounded-xl border border-red-500/30 group-hover:shadow-[0_0_20px_rgba(220,38,38,0.5)] transition-shadow">
                        <GraduationCap className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-white via-red-100 to-zinc-400 bg-clip-text text-transparent">
                            CBC Expert
                        </h1>
                        <p className="text-[10px] text-zinc-500 font-medium tracking-[0.2em] uppercase">Transition Guide</p>
                    </div>
                </Link>

                {/* Desktop Nav */}
                <div className="hidden md:flex items-center gap-8">
                    {navLinks.map((link) => (
                        <Link
                            key={link.name}
                            href={link.href}
                            className={`text-sm font-medium transition-colors ${isActive(link.href)
                                    ? "text-red-500"
                                    : "text-zinc-400 hover:text-white"
                                }`}
                        >
                            {link.name}
                        </Link>
                    ))}
                    <Link
                        href="/contact"
                        className="px-5 py-2.5 bg-white text-black text-sm font-bold rounded-full hover:bg-zinc-200 transition-colors"
                    >
                        Get Help
                    </Link>
                </div>

                {/* Mobile Menu Button */}
                <button
                    className="md:hidden p-2 text-zinc-400 hover:text-white"
                    onClick={() => setIsOpen(!isOpen)}
                >
                    {isOpen ? <X /> : <Menu />}
                </button>
            </div>

            {/* Mobile Menu */}
            {isOpen && (
                <div className="md:hidden absolute top-20 left-0 w-full bg-zinc-950 border-b border-white/10 p-6 flex flex-col gap-4">
                    {navLinks.map((link) => (
                        <Link
                            key={link.name}
                            href={link.href}
                            onClick={() => setIsOpen(false)}
                            className={`text-lg font-medium ${isActive(link.href) ? "text-red-500" : "text-zinc-400"
                                }`}
                        >
                            {link.name}
                        </Link>
                    ))}
                </div>
            )}
        </nav>
    );
}
