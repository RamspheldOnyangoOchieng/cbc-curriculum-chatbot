import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";
import { ChromaClient } from "chromadb";
import { KNOWLEDGE_BASE } from "@/lib/knowledge";

const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY,
});

// Helper to get embeddings from Hugging Face (matches backend)
async function getQueryEmbedding(text: string) {
    const hfToken = process.env.HUGGINGFACE_TOKEN;
    if (!hfToken) {
        console.error("Missing HUGGINGFACE_TOKEN in Vercel.");
        return null;
    }

    try {
        const response = await fetch(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${hfToken}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ inputs: [text], options: { wait_for_model: true } }),
            }
        );
        const result = await response.json();
        return result[0]; // Returns the embedding vector
    } catch (err) {
        console.error("Embedding failed:", err);
        return null;
    }
}

export async function POST(req: NextRequest) {
    try {
        const { messages } = await req.json();
        const userQuery = messages[messages.length - 1]?.content || "";

        // 1. RAG: Fetch relevant context from ChromaCloud (v2 API)
        let context = "";
        try {
            console.log("RAG: Embedding query...");
            const queryEmbedding = await getQueryEmbedding(userQuery);

            if (queryEmbedding) {
                console.log("RAG: Searching Chroma Cloud via v2 API...");
                const host = (process.env.CHROMA_HOST || "https://api.trychroma.com").replace(/\/$/, "");
                const tenant = process.env.CHROMA_TENANT || "default_tenant";
                const database = process.env.CHROMA_DATABASE || "default_database";
                const apiKey = process.env.CHROMA_API_KEY;

                // A. Get Collection ID
                const listUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections`;
                const listResp = await fetch(listUrl, {
                    headers: { "x-chroma-token": apiKey || "" }
                });
                const collections = await listResp.json();
                const collection = collections.find((c: any) => c.name === "Curriculumnpdfs");

                if (collection) {
                    // B. Query Vector
                    const queryUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections/${collection.id}/query`;
                    const queryResp = await fetch(queryUrl, {
                        method: "POST",
                        headers: {
                            "x-chroma-token": apiKey || "",
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            query_embeddings: [queryEmbedding],
                            n_results: 2,
                        })
                    });
                    const results = await queryResp.json();

                    if (results.documents && results.documents[0]) {
                        const docs = results.documents[0].filter((doc: any): doc is string => doc !== null);
                        context = docs.join("\n\n---\n\n");
                        console.log(`RAG: Found ${docs.length} context chunks.`);
                    }
                } else {
                    console.warn("RAG: Collection 'Curriculumnpdfs' not found in Cloud.");
                }
            } else {
                console.warn("RAG: Skipping retrieval because embedding failed.");
            }
        } catch (ragError) {
            console.warn("RAG retrieval failed:", ragError);
        }

        // 2. Construct Consolidated System Prompt
        const systemPromptContent = `
${KNOWLEDGE_BASE.SYSTEM_PROMPT_START}

${KNOWLEDGE_BASE.CRITICAL_RULES}

CONTEXT FROM KNOWLEDGE BASE:
${context ? context : "No specific documents found. Use your general knowledge and the Key Context provided above."}
        `.trim();

        const systemPrompt = {
            role: "system" as const,
            content: systemPromptContent
        };

        // 3. Call Groq
        const chatCompletion = await groq.chat.completions.create({
            messages: [systemPrompt, ...messages],
            model: "llama-3.3-70b-versatile",
            temperature: 0.7,
            max_tokens: 1024,
            top_p: 1,
            stream: false,
        });

        const responseContent = chatCompletion.choices[0]?.message?.content || "I'm sorry, I couldn't generate a response at this time.";

        return NextResponse.json({
            role: "assistant",
            content: responseContent
        });

    } catch (error: any) {
        console.error("Error in chat API:", error);
        return NextResponse.json({ error: error.message || "Internal Server Error" }, { status: 500 });
    }
}


