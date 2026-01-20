"use client";

import React, { useState } from "react";
import { Mail, Phone, MapPin, Send, MessageSquare, Building2, Globe } from "lucide-react";

export default function ContactPage() {
    const [formState, setFormState] = useState({ name: "", email: "", message: "" });
    const [status, setStatus] = useState<"idle" | "sending" | "success">("idle");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setStatus("sending");
        // Simulate finding
        setTimeout(() => {
            setStatus("success");
            setFormState({ name: "", email: "", message: "" });
        }, 1500);
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-zinc-100 font-sans p-8 pb-32">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <header className="mb-16 text-center">
                    <div className="inline-block px-4 py-1.5 mb-6 rounded-full bg-zinc-800 border border-zinc-700 text-zinc-300 text-sm font-semibold tracking-wider uppercase">
                        Support Center
                    </div>
                    <h1 className="text-4xl md:text-6xl font-extrabold mb-6">
                        Get <span className="text-red-500">Help</span>
                    </h1>
                    <p className="text-xl text-zinc-400 max-w-2xl mx-auto">
                        Have questions about Grade 10 transitions or the CBC curriculum? We are here to guide you.
                    </p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    {/* Contact Form */}
                    <div className="bg-zinc-900/50 border border-white/5 rounded-3xl p-8">
                        <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                            <MessageSquare className="w-6 h-6 text-red-500" />
                            Send us a Message
                        </h3>

                        {status === "success" ? (
                            <div className="h-64 flex flex-col items-center justify-center text-center p-6 bg-green-900/20 rounded-2xl border border-green-500/30">
                                <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mb-4">
                                    <Send className="w-8 h-8 text-white" />
                                </div>
                                <h4 className="text-xl font-bold text-white mb-2">Message Sent!</h4>
                                <p className="text-zinc-400">Thank you for reaching out. Our expert team will get back to you shortly.</p>
                                <button onClick={() => setStatus("idle")} className="mt-6 text-green-400 hover:text-green-300 font-medium">Send another message</button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-zinc-400">Full Name</label>
                                    <input
                                        required
                                        type="text"
                                        value={formState.name}
                                        onChange={(e) => setFormState({ ...formState, name: e.target.value })}
                                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 focus:outline-none focus:border-red-500/50 transition-all"
                                        placeholder="John Doe"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-zinc-400">Email Address</label>
                                    <input
                                        required
                                        type="email"
                                        value={formState.email}
                                        onChange={(e) => setFormState({ ...formState, email: e.target.value })}
                                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 focus:outline-none focus:border-red-500/50 transition-all"
                                        placeholder="john@example.com"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-zinc-400">Your Message</label>
                                    <textarea
                                        required
                                        rows={4}
                                        value={formState.message}
                                        onChange={(e) => setFormState({ ...formState, message: e.target.value })}
                                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 focus:outline-none focus:border-red-500/50 transition-all resize-none"
                                        placeholder="How can we help you today?"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={status === "sending"}
                                    className="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                                >
                                    {status === "sending" ? "Sending..." : "Send Message"}
                                    {!status && <Send className="w-4 h-4" />}
                                </button>
                            </form>
                        )}
                    </div>

                    {/* Contact Info & Official Channels */}
                    <div className="space-y-8">
                        {/* Official KICD Info */}
                        <div className="p-8 rounded-3xl bg-zinc-900 border border-zinc-800">
                            <h3 className="text-xl font-bold mb-6 flex items-center gap-2 text-zinc-200">
                                <Building2 className="w-5 h-5 text-amber-500" />
                                Official KICD Headquarters
                            </h3>
                            <div className="space-y-6 text-zinc-400">
                                <div className="flex items-start gap-4">
                                    <MapPin className="w-5 h-5 mt-1 shrink-0" />
                                    <p>Kenya Institute of Curriculum Development<br />Desai Rd, Off Muranga Rd<br />Nairobi, Kenya</p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <Phone className="w-5 h-5 shrink-0" />
                                    <p>+254 (020) 3749900-9</p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <Mail className="w-5 h-5 shrink-0" />
                                    <p>info@kicd.ac.ke</p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <Globe className="w-5 h-5 shrink-0" />
                                    <a href="https://kicd.ac.ke" target="_blank" className="text-red-400 hover:text-red-300 transition-colors">www.kicd.ac.ke</a>
                                </div>
                            </div>
                        </div>

                        {/* FAQ Quick Links */}
                        <div className="p-8 rounded-3xl bg-zinc-950 border border-zinc-800">
                            <h3 className="text-xl font-bold mb-4 text-zinc-200">Common Questions</h3>
                            <ul className="space-y-3">
                                <li>
                                    <button className="text-left text-zinc-400 hover:text-white transition-colors w-full flex items-center justify-between group">
                                        <span>How do I change my child's pathway?</span>
                                        <span className="text-zinc-600 group-hover:text-red-500">→</span>
                                    </button>
                                </li>
                                <li className="w-full h-px bg-white/5" />
                                <li>
                                    <button className="text-left text-zinc-400 hover:text-white transition-colors w-full flex items-center justify-between group">
                                        <span>Where can I find grade 10 book lists?</span>
                                        <span className="text-zinc-600 group-hover:text-red-500">→</span>
                                    </button>
                                </li>
                                <li className="w-full h-px bg-white/5" />
                                <li>
                                    <button className="text-left text-zinc-400 hover:text-white transition-colors w-full flex items-center justify-between group">
                                        <span>Report a missing placement?</span>
                                        <span className="text-zinc-600 group-hover:text-red-500">→</span>
                                    </button>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
