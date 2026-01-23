import { NextRequest, NextResponse } from "next/server";

/**
 * OPTION A: PROXY TO RENDER BACKEND
 * This route sends the chat request to the Python FastAPI backend on Render.
 */
export async function POST(req: NextRequest) {
    try {
        const body = await req.json();

        // Use environment variable or fallback to your specific Render URL
        const BACKEND_URL = process.env.PYTHON_BACKEND_URL || "https://cbc-curriculum-chatbot.onrender.com";
        const targetUrl = `${BACKEND_URL.replace(/\/$/, "")}/chat`;

        console.log(`Forwarding chat request to: ${targetUrl}`);

        const response = await fetch(targetUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Backend returned error (${response.status}):`, errorText);
            return NextResponse.json(
                { error: "The CBC backend is currently unavailable. Please try again in a moment." },
                { status: response.status }
            );
        }

        const data = await response.json();

        // Return the data directly to the frontend components
        return NextResponse.json(data);

    } catch (error: any) {
        console.error("Critical Proxy Error:", error);
        return NextResponse.json(
            { error: "Network error: Unable to connect to CBC Backend." },
            { status: 500 }
        );
    }
}
