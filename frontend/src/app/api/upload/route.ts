import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    try {
        const formData = await req.formData();
        const file = formData.get("file") as File | null;
        const textContent = formData.get("text") as string | null;
        const title = formData.get("title") as string | null;

        const backendUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

        if (file) {
            // Forward Request to Python Backend /ingest
            const backendFormData = new FormData();
            backendFormData.append("file", file);

            const response = await fetch(`${backendUrl}/ingest`, {
                method: "POST",
                body: backendFormData,
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Backend Error: ${errorText}`);
            }

            const data = await response.json();
            return NextResponse.json({ success: true, message: data.message, type: 'file' });

        } else if (textContent && title) {
            // Forward Request to Python Backend /ingest-text
            const response = await fetch(`${backendUrl}/ingest-text`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ title, text: textContent })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Backend Error: ${errorText}`);
            }

            const data = await response.json();
            return NextResponse.json({ success: true, message: "Text content ingested successfully.", type: 'text' });
        } else if (formData.get("url")) {
            const url = formData.get("url") as string;
            // Forward Request to Python Backend /ingest-url
            const response = await fetch(`${backendUrl}/ingest-url`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Backend Error: ${errorText}`);
            }

            const data = await response.json();
            return NextResponse.json({ success: true, message: data.message, type: 'url' });
        }

        return NextResponse.json({ error: "No valid data provided" }, { status: 400 });

    } catch (error: any) {
        console.error("Upload error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
