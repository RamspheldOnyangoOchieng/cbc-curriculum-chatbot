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
    if (!hfToken) return { vector: null, error: "MISSING_TOKEN" };

    try {
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
        if (result.error) return { vector: null, error: "HF_API_ERROR" };
        return { vector: Array.isArray(result) ? result[0] : null, error: null };
    } catch (err) {
        return { vector: null, error: "FETCH_EXCEPTION" };
    }
}

export async function POST(req: NextRequest) {
    let ragStatus = "SKIPPED";
    try {
        const { messages } = await req.json();
        const userQuery = messages[messages.length - 1]?.content || "";

        // 1. RAG Chain
        let contextData: string[] = [];
        try {
            const { vector: queryEmbedding, error: embError } = await getQueryEmbedding(userQuery);

            if (queryEmbedding) {
                const host = (process.env.CHROMA_HOST || "https://api.trychroma.com").replace(/\/$/, "");
                const tenant = process.env.CHROMA_TENANT || "bb042f26-2c1c-4c18-844b-a569ea3944b4";
                const database = process.env.CHROMA_DATABASE || "cbc-chatbot";
                const apiKey = process.env.CHROMA_API_KEY;

                // A. Direct Collection Access
                const collUrl = `${host}/api/v2/tenants/${tenant}/databases/${database}/collections/Curriculumnpdfs`;
                const collResp = await fetch(collUrl, { headers: { "x-chroma-token": apiKey || "" } });

                if (collResp.ok) {
                    const collection = await collResp.json();

                    // B. Query
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
                            include: ["documents"]
                        })
                    });

                    const results = await queryResp.json();
                    if (results && results.documents && results.documents[0]) {
                        contextData = results.documents[0].filter((d: any) => d !== null);
                        ragStatus = contextData.length > 0 ? "SUCCESS" : "ZERO_DOCS_FOUND";
                    } else {
                        ragStatus = "MALFORMED_CHROMA_RESPONSE";
                    }
                } else {
                    ragStatus = `COLLECTION_FETCH_FAILED_${collResp.status}`;
                }
            } else {
                ragStatus = embError || "EMBEDDING_FAILED";
            }
        } catch (ragError) {
            console.error("RAG logic error:", ragError);
            ragStatus = "RAG_RUNTIME_CRASH";
        }

        const contextString = contextData.length > 0 ? contextData.join("\n\n---\n\n") : "";

        // 2. Synthesize
        const systemPromptContent = `
${KNOWLEDGE_BASE.SYSTEM_PROMPT_START}
${KNOWLEDGE_BASE.CRITICAL_RULES}

DOCUMENTS FROM KNOWLEDGE BASE:
${contextString || "NO RELEVANT DOCUMENTS FOUND."}
        `.trim();

        const chatCompletion = await groq.chat.completions.create({
            messages: [{ role: "system", content: systemPromptContent }, ...messages],
            model: "llama-3.3-70b-versatile",
            temperature: 0.1,
            max_tokens: 1500,
        });

        const responseContent = chatCompletion.choices[0]?.message?.content || "No response generated.";

        // FOOTER FOR US TO DEBUG
        const debugFooter = `\n\n[System_RAG: ${ragStatus} | Context_Size: ${contextData.length}]`;

        return NextResponse.json({
            role: "assistant",
            content: responseContent + debugFooter
        });

    } catch (error: any) {
        console.error("Chat API Critical failure:", error);
        return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
    }
}




