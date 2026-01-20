import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";
import { ChromaClient } from "chromadb";
import { KNOWLEDGE_BASE } from "@/lib/knowledge";

const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY,
});

// 1. Instant Tokenizer: Creates word-by-word variations + key phrases instantly
function getExpandedQueries(text: string) {
    const clean = text.replace(/[?.,!]/g, "").toLowerCase();
    const words = clean.split(/\s+/).filter(w => w.length > 3); // Significant words
    const variations = [
        text, // Full Query
        `CBC curriculum ${text}`, // Contextualized
        ...words.slice(0, 8) // Individual Word Drills (top 8)
    ];
    return Array.from(new Set(variations)); // Unique intents
}

// 2. Optimized Batch Embedding (Parallelized)
async function getBatchEmbeddings(queries: string[]) {
    const hfToken = process.env.HUGGINGFACE_TOKEN;
    if (!hfToken) return [];

    try {
        const prefixedQueries = queries.map(q => `Represent this educational term for retrieval: ${q}`);
        const response = await fetch(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            {
                method: "POST",
                headers: { Authorization: `Bearer ${hfToken}`, "Content-Type": "application/json" },
                body: JSON.stringify({ inputs: prefixedQueries, options: { wait_for_model: true } }),
            }
        );
        const result = await response.json();
        return Array.isArray(result) ? result : [];
    } catch (err) {
        console.error("Batch Embedding Err:", err);
        return [];
    }
}

// Helper for parallelized retrieval
async function multiSearch(vectors: any[], host: string, tenant: string, database: string, apiKey: string, collId: string) {
    const queryUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections/${collId}/query`;
    const resp = await fetch(queryUrl, {
        method: "POST",
        headers: { "x-chroma-token": apiKey, "Content-Type": "application/json" },
        body: JSON.stringify({
            query_embeddings: vectors,
            n_results: 10, // Max breadth per word-drill
            include: ["documents"]
        })
    });
    return await resp.json();
}

export async function POST(req: NextRequest) {
    const startTime = Date.now();
    let debugInfo = { mode: "DRILL_SEARCH", depth: 0, time: 0 };

    try {
        const { messages } = await req.json();
        const userQuery = messages[messages.length - 1]?.content || "";

        const host = (process.env.CHROMA_HOST || "https://api.trychroma.com").replace(/\/$/, "");
        const tenant = process.env.CHROMA_TENANT || "bb042f26-2c1c-4c18-844b-a569ea3944b4";
        const database = process.env.CHROMA_DATABASE || "cbc-chatbot";
        const apiKey = process.env.CHROMA_API_KEY || "";

        // 1. SEMANTIC MEMORY FIRST (Lightning Fast)
        let contextData: string[] = [];
        const baseEmbeddings = await getBatchEmbeddings([userQuery]);

        if (baseEmbeddings.length > 0) {
            try {
                // Check if we have a similar past question in 'ChatMemory'
                const memUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections/ChatMemory/query`;
                const memResp = await fetch(memUrl, {
                    method: "POST",
                    headers: { "x-chroma-token": apiKey, "Content-Type": "application/json" },
                    body: JSON.stringify({
                        query_embeddings: [baseEmbeddings[0]],
                        n_results: 1,
                        include: ["documents", "distances"]
                    })
                });

                if (memResp.ok) {
                    const memResult = await memResp.json();
                    if (memResult.distances && memResult.distances[0] && memResult.distances[0][0] < 0.1) {
                        contextData = [memResult.documents[0][0]];
                        debugInfo.mode = "CACHE_HIT";
                    }
                }
            } catch (e) { console.error("Memory Cache Error:", e); }
        }

        // 2. DRILL & SWEEP (If cache missed)
        if (contextData.length === 0) {
            debugInfo.mode = "WORD_DRILL";
            // Parallel intent expansion (Instant) + Collection Check
            const variations = getExpandedQueries(userQuery);
            const [vectors, collResp] = await Promise.all([
                getBatchEmbeddings(variations),
                fetch(`${host}/api/v2/tenants/${tenant}/databases/${database}/collections/Curriculumnpdfs`, {
                    headers: { "x-chroma-token": apiKey }
                })
            ]);

            if (collResp.ok && vectors.length > 0) {
                const collection = await collResp.json();
                const results = await multiSearch(vectors, host, tenant, database, apiKey, collection.id);

                const seen = new Set();
                if (results.documents) {
                    results.documents.forEach((docList: any) => {
                        docList.filter((d: any) => d !== null).forEach((d: string) => {
                            const fingerprint = d.slice(0, 150);
                            if (!seen.has(fingerprint)) {
                                contextData.push(d);
                                seen.add(fingerprint);
                            }
                        });
                    });
                }
            }
        }

        debugInfo.depth = contextData.length;
        const contextString = contextData.join("\n\n---\n\n");

        // 3. SYNTHESIZE
        const systemPrompt = `
${KNOWLEDGE_BASE.SYSTEM_PROMPT_START}
${KNOWLEDGE_BASE.CRITICAL_RULES}

ACT AS A CBC EXPERT REFINER.
A word-by-word deep drill of the database has retrieved many fragments.
Your goal is to synthesize these related "scraps" into a definitive and professional answer.

DATABASE FRAGMENTS:
${contextString || "NO SPECIFIC SCRAPS RETRIEVED. Use general CBC expert terminology."}
        `.trim();

        const chatCompletion = await groq.chat.completions.create({
            messages: [{ role: "system", content: systemPrompt }, ...messages],
            model: "llama-3.3-70b-versatile",
            temperature: 0.2,
            max_tokens: 1500,
        });

        const responseContent = chatCompletion.choices[0]?.message?.content || "";
        debugInfo.time = Date.now() - startTime;

        // 4. PERSIST TO MEMORY (Background)
        if (debugInfo.mode === "WORD_DRILL" && responseContent && baseEmbeddings[0]) {
            fetch(`${host}/api/v2/tenants/${tenant}/databases/${database}/collections/ChatMemory/upsert`, {
                method: "POST",
                headers: { "x-chroma-token": apiKey, "Content-Type": "application/json" },
                body: JSON.stringify({
                    ids: [`mem_${Date.now()}`],
                    embeddings: [baseEmbeddings[0]],
                    documents: [responseContent],
                    metadatas: [{ question: userQuery }]
                })
            }).catch(() => { });
        }

        return NextResponse.json({
            role: "assistant",
            content: responseContent
        });

    } catch (error: any) {
        console.error("Critical Chat Error:", error);
        return NextResponse.json({ error: "Internal Error" }, { status: 500 });
    }
}







