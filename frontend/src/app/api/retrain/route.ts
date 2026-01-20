import { NextResponse } from "next/server";

export async function POST() {
    return NextResponse.json({
        success: true,
        message: "Retraining is now handled automatically when you upload files. No manual action needed."
    });
}
