import { NextRequest, NextResponse } from "next/server";
import Groq from "groq-sdk";
import { ChromaClient } from "chromadb";
import { KNOWLEDGE_BASE } from "@/lib/knowledge";

const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY,
});

// Helper to get embeddings from Hugging Face
async function getQueryEmbedding(text: string) {
    const hfToken = process.env.HUGGINGFACE_TOKEN;
    if (!hfToken) return null;

    try {
        // BGE models work significantly better when the query is prefixed
        const prefixedQuery = `Represent this query for retrieving relevant documents: ${text}`;

        const response = await fetch(
            "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5",
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${hfToken}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ inputs: [prefixedQuery], options: { wait_for_model: true } }),
            }
        );
        const result = await response.json();
        return Array.isArray(result) ? result[0] : null;
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
        let contextData: string[] = [];
        try {
            const queryEmbedding = await getQueryEmbedding(userQuery);

            if (queryEmbedding) {
                const host = (process.env.CHROMA_HOST || "https://api.trychroma.com").replace(/\/$/, "");
                const tenant = process.env.CHROMA_TENANT || "bb042f26-2c1c-4c18-844b-a569ea3944b4";
                const database = process.env.CHROMA_DATABASE || "cbc-chatbot";
                const apiKey = process.env.CHROMA_API_KEY;

                // Step A: Find the collection ID
                const listUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections`;
                const listResp = await fetch(listUrl, { headers: { "x-chroma-token": apiKey || "" } });
                const collections = await listResp.json();
                const collection = Array.isArray(collections) ? collections.find((c: any) => c.name === "Curriculumnpdfs") : null;

                if (collection) {
                    // Step B: Query with vectors
                    const queryUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections/${collection.id}/query`;
                    const queryResp = await fetch(queryUrl, {
                        method: "POST",
                        headers: {
                            "x-chroma-token": apiKey || "",
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            query_embeddings: [queryEmbedding],
                            n_results: 3,
                            include: ["documents", "metadatas"]
                        })
                    });

                    const results = await queryResp.json();

                    // Correct v2 response parsing (results.documents is usually a nested array)
                    if (results && results.documents && results.documents[0]) {
                        contextData = results.documents[0].filter((d: any) => d !== null);
                        console.log(`RAG: Successfully retrieved ${contextData.length} documents.`);
                    }
                }
            }
        } catch (ragError) {
            console.warn("RAG retrieval chain failed:", ragError);
        }

        const contextString = contextData.length > 0
            ? contextData.join("\n\n---\n\n")
            : "No related documents found. Use provided system knowledge only.";

        // 2. Build the LLM prompt with strict context enforcement
        const systemPromptContent = `
${KNOWLEDGE_BASE.SYSTEM_PROMPT_START}

${KNOWLEDGE_BASE.CRITICAL_RULES}

CRITICAL: You MUST prioritize information from the "DOCUMENTS FROM KNOWLEDGE BASE" section below. 
If the documents explain a term (like KJSEA), use that definition even if your general training data says otherwise.

DOCUMENTS FROM KNOWLEDGE BASE:
${contextString}
        `.trim();

        const systemPrompt = {
            role: "system" as const,
            content: systemPromptContent
        };

        // 3. Generate response using Groq
        const chatCompletion = await groq.chat.completions.create({
            messages: [systemPrompt, ...messages],
            model: "llama-3.3-70b-versatile",
            temperature: 0.1, // Lower temperature for more factual accuracy
            max_tokens: 1500,
            stream: false,
        });

        const responseContent = chatCompletion.choices[0]?.message?.content || "I'm having trouble retrieving an answer.";

        return NextResponse.json({
            role: "assistant",
            content: responseContent
        });

    } catch (error: any) {
        console.error("Critical Chat API Error:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}



