const { ChromaClient } = require("chromadb");
require("dotenv").config({ path: "../.env" });

async function checkCount() {
    try {
        const client = new ChromaClient({
            path: process.env.CHROMA_HOST,
            tenant: process.env.CHROMA_TENANT,
            database: process.env.CHROMA_DATABASE,
            auth: {
                provider: "token",
                credentials: process.env.CHROMA_API_KEY,
                tokenHeader: "Authorization"
            }
        });

        const collection = await client.getCollection({ name: "Curriculumnpdfs" });
        const count = await collection.count();
        console.log(`Current items in 'Curriculumnpdfs': ${count}`);
    } catch (error) {
        console.error("Error checking count:", error.message);
    }
}

checkCount();
