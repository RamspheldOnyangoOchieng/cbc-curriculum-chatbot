import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";
import { ChromaClient } from "chromadb";
import { KNOWLEDGE_BASE } from "@/lib/knowledge";

const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY,
});

// 1. Triple-Query Expansion: Generate 3 variations for deeper breadth
async function getExpandedQueries(text: string) {
    try {
        const prompt = `Convert this CBC question into 3 distinct search keywords or educational phrases for retrieval. Return ONLY a JSON object with key "variations" showing an array of strings. Query: "${text}"`;
        const completion = await groq.chat.completions.create({
            messages: [{ role: "user", content: prompt }],
            model: "llama-3.1-8b-instant", // Very fast for intent expansion
            temperature: 0,
            response_format: { type: "json_object" }
        });
        const content = completion.choices[0]?.message?.content || "{}";
        const parsed = JSON.parse(content);
        return Array.isArray(parsed.variations) ? parsed.variations.slice(0, 3) : [text];
    } catch (e) {
        return [text];
    }
}

// 2. Fast Batch Embedding
async function getBatchEmbeddings(queries: string[]) {
    const hfToken = process.env.HUGGINGFACE_TOKEN;
    if (!hfToken) return [];

    try {
        const prefixedQueries = queries.map(q => `Represent this educational query for retrieval: ${q}`);
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
            n_results: 5,
            include: ["documents"]
        })
    });
    return await resp.json();
}

export async function POST(req: NextRequest) {
    const startTime = Date.now();
    let debugInfo = { mode: "DRILL_SWEEP", depth: 0, time: 0 };

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
                    // If we found a NEAR PERFECT match (distance < 0.1), use it!
                    if (memResult.distances && memResult.distances[0] && memResult.distances[0][0] < 0.1) {
                        contextData = [memResult.documents[0][0]];
                        debugInfo.mode = "CACHE_HIT";
                    }
                }
            } catch (e) { console.error("Memory Cache Error:", e); }
        }

        // 2. DRILL & SWEEP (If cache missed)
        if (contextData.length === 0) {
            // Run Expansion and Collection lookup in PARALLEL to boost speed
            const [variations, collResp] = await Promise.all([
                getExpandedQueries(userQuery),
                fetch(`${host}/api/v2/tenants/${tenant}/databases/${database}/collections/Curriculumnpdfs`, {
                    headers: { "x-chroma-token": apiKey }
                })
            ]);

            if (collResp.ok) {
                const collection = await collResp.json();
                const vectors = await getBatchEmbeddings(variations);
                const results = await multiSearch(vectors, host, tenant, database, apiKey, collection.id);

                const seen = new Set();
                if (results.documents) {
                    results.documents.forEach((docList: any) => {
                        docList.filter((d: any) => d !== null).forEach((d: string) => {
                            if (!seen.has(d.slice(0, 100))) {
                                contextData.push(d);
                                seen.add(d.slice(0, 100));
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
Provide a high-quality answer based on these database segments:
${contextString || "USE YOUR GENERAL TERMINOLOGY FOR CBC."}
        `.trim();

        const chatCompletion = await groq.chat.completions.create({
            messages: [{ role: "system", content: systemPrompt }, ...messages],
            model: "llama-3.3-70b-versatile",
            temperature: 0.2,
            max_tokens: 1500,
        });

        const responseContent = chatCompletion.choices[0]?.message?.content || "";
        debugInfo.time = Date.now() - startTime;

        // 4. PERSIST TO MEMORY (Background - don't wait)
        if (debugInfo.mode === "DRILL_SWEEP" && responseContent && baseEmbeddings[0]) {
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
            content: responseContent + `\n\n[Mode: ${debugInfo.mode} | Scraps: ${debugInfo.depth} | Speed: ${debugInfo.time}ms]`
        });

    } catch (error: any) {
        console.error("Critical Chat Error:", error);
        return NextResponse.json({ error: "Internal Error" }, { status: 500 });
    }
}







