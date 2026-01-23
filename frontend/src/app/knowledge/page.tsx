"use client";

import React, { useState } from "react";
import { Upload, FileText, Database, CheckCircle, AlertCircle, Loader2, Link as LinkIcon } from "lucide-react";
import { motion } from "framer-motion";

export default function KnowledgePage() {
    const [activeTab, setActiveTab] = useState<"upload" | "paste" | "link">("upload");
    const [file, setFile] = useState<File | null>(null);
    const [textTitle, setTextTitle] = useState("");
    const [textContent, setTextContent] = useState("");
    const [url, setUrl] = useState("");
    const [status, setStatus] = useState<"idle" | "uploading" | "retraining" | "success" | "error">("idle");
    const [logs, setLogs] = useState<string>("");

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async () => {
        setStatus("uploading");
        setLogs("");
        const formData = new FormData();

        try {
            // 1. Upload Phase
            if (activeTab === "upload" && file) {
                formData.append("file", file);
            } else if (activeTab === "paste" && textContent && textTitle) {
                formData.append("text", textContent);
                formData.append("title", textTitle);
            } else if (activeTab === "link" && url) {
                formData.append("url", url);
            } else {
                throw new Error("Please provide valid input.");
            }

            const uploadRes = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });

            if (!uploadRes.ok) throw new Error("Upload failed");
            const uploadData = await uploadRes.json();
            setLogs((prev) => prev + `> ${uploadData.message}\n`);

            // 2. Retraining Phase
            setStatus("retraining");
            setLogs((prev) => prev + "> Starting RAG retraining (this may take a minute)...\n");

            const retrainRes = await fetch("/api/retrain", {
                method: "POST",
            });

            const retrainData = await retrainRes.json();

            if (!retrainRes.ok) {
                setLogs((prev) => prev + `ERROR:\n${retrainData.details}\n`);
                throw new Error("Retraining failed");
            }

            setLogs((prev) => prev + "--------------------------------\n" + retrainData.logs);
            setStatus("success");

        } catch (error: any) {
            console.error(error);
            setStatus("error");
            setLogs((prev) => prev + `\nCRITICAL ERROR: ${error.message}`);
        }
    };

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-zinc-100 font-sans p-8">
            <div className="max-w-4xl mx-auto">
                <header className="mb-10">
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-red-500 to-amber-500 bg-clip-text text-transparent mb-2">
                        Knowledge Base Manager
                    </h1>
                    <p className="text-zinc-600">Update the chatbot's brain with new PDF documents or raw text.</p>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Input Section */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-zinc-900/50 border border-white/5 rounded-2xl p-1">
                            <div className="grid grid-cols-3 gap-1 mb-6">
                                <button
                                    onClick={() => setActiveTab("upload")}
                                    className={`flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === "upload" ? "bg-zinc-800 text-white shadow-lg" : "text-zinc-500 hover:text-zinc-300"
                                        }`}
                                >
                                    <Upload className="w-4 h-4" /> PDF
                                </button>
                                <button
                                    onClick={() => setActiveTab("paste")}
                                    className={`flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === "paste" ? "bg-zinc-800 text-white shadow-lg" : "text-zinc-500 hover:text-zinc-300"
                                        }`}
                                >
                                    <FileText className="w-4 h-4" /> Text
                                </button>
                                <button
                                    onClick={() => setActiveTab("link")}
                                    className={`flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === "link" ? "bg-zinc-800 text-white shadow-lg" : "text-zinc-500 hover:text-zinc-300"
                                        }`}
                                >
                                    <LinkIcon className="w-4 h-4" /> Link
                                </button>
                            </div>

                            <div className="p-4">
                                {activeTab === "upload" ? (
                                    <div className="border-2 border-dashed border-zinc-700 rounded-xl p-10 text-center hover:border-zinc-500 transition-colors">
                                        <input
                                            type="file"
                                            accept=".pdf"
                                            onChange={handleFileChange}
                                            className="hidden"
                                            id="file-upload"
                                        />
                                        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-4">
                                            <div className="p-4 bg-zinc-800 rounded-full">
                                                <Upload className="w-8 h-8 text-zinc-400" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-lg">Click to select PDF</p>
                                                <p className="text-sm text-zinc-500 mt-1">{file ? file.name : "Supports .pdf only"}</p>
                                            </div>
                                        </label>
                                    </div>
                                ) : activeTab === "paste" ? (
                                    <div className="space-y-4">
                                        <input
                                            type="text"
                                            placeholder="Title (e.g., Grade 10 Math Syllabus)"
                                            value={textTitle}
                                            onChange={(e) => setTextTitle(e.target.value)}
                                            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 focus:outline-none focus:border-red-500/50 transition-all"
                                        />
                                        <textarea
                                            placeholder="Paste your content here..."
                                            value={textContent}
                                            onChange={(e) => setTextContent(e.target.value)}
                                            className="w-full h-64 bg-zinc-950 border border-zinc-800 rounded-xl p-4 focus:outline-none focus:border-red-500/50 transition-all resize-none"
                                        />
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <input
                                            type="url"
                                            placeholder="Paste URL (e.g., https://thekenyatimes.com/...)"
                                            value={url}
                                            onChange={(e) => setUrl(e.target.value)}
                                            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 focus:outline-none focus:border-red-500/50 transition-all"
                                        />
                                        <div className="p-8 bg-zinc-800/20 border border-dashed border-zinc-800 rounded-xl text-center">
                                            <LinkIcon className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
                                            <p className="text-sm text-zinc-500">The system will deeply scrape this URL and add it to the knowledge base.</p>
                                        </div>
                                    </div>
                                )}

                                <button
                                    onClick={handleSubmit}
                                    disabled={status === "uploading" || status === "retraining"}
                                    className="w-full mt-6 bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl flex items-center justify-center gap-2 transition-all"
                                >
                                    {status === "uploading" || status === "retraining" ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <Database className="w-5 h-5" />
                                    )}
                                    {status === "uploading" ? "Uploading..." : status === "retraining" ? "Retraining Model..." : "Add & Retrain"}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Status & Logs */}
                    <div className="bg-zinc-950 rounded-2xl border border-white/5 p-6 h-[600px] flex flex-col">
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${status === 'success' ? 'bg-green-500' : status === 'error' ? 'bg-red-500' : status !== 'idle' ? 'bg-amber-500 animate-pulse' : 'bg-zinc-700'}`} />
                            System Status
                        </h3>

                        <div className="flex-1 bg-black rounded-xl p-4 font-mono text-xs text-zinc-400 overflow-y-auto whitespace-pre-wrap border border-white/5">
                            {logs || "System ready. Waiting for input..."}
                        </div>

                        {status === "success" && (
                            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 p-4 bg-green-900/20 border border-green-500/20 rounded-xl flex items-center gap-3">
                                <CheckCircle className="w-5 h-5 text-green-500" />
                                <p className="text-sm text-green-200">Knowledge update complete!</p>
                            </motion.div>
                        )}
                        {status === "error" && (
                            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-4 p-4 bg-red-900/20 border border-red-500/20 rounded-xl flex items-center gap-3">
                                <AlertCircle className="w-5 h-5 text-red-500" />
                                <p className="text-sm text-red-200">Update failed. Check logs.</p>
                            </motion.div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
