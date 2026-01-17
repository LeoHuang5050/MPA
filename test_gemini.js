
const { GoogleGenerativeAI } = require("@google/generative-ai");
const fs = require('fs');
const path = require('path');

// Load env simply
let apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) {
    try {
        const envPath = path.resolve(__dirname, 'packages/nextjs/.env.local');
        const envContent = fs.readFileSync(envPath, 'utf8');
        const match = envContent.match(/GEMINI_API_KEY=(.*)/);
        if (match) apiKey = match[1].trim();
    } catch (e) {
        console.log("No .env.local found or readable");
    }
}

console.log("Testing with Key:", apiKey ? "FOUND (Starts with " + apiKey.substring(0, 4) + ")" : "NOT FOUND");

if (!apiKey) {
    console.error("Please set GEMINI_API_KEY in packages/nextjs/.env.local");
    process.exit(1);
}

const genAI = new GoogleGenerativeAI(apiKey);

async function testModel(modelName) {
    console.log(`\n--- Testing ${modelName} ---`);
    try {
        const model = genAI.getGenerativeModel({ model: modelName });
        const result = await model.generateContent("Hello, are you there?");
        const response = result.response;
        console.log("SUCCESS! Output:", response.text());
        return true;
    } catch (error) {
        console.error("FAILED:", error.message);
        return false;
    }
}

async function run() {
    await testModel("gemini-1.5-flash");
    await testModel("gemini-2.0-flash-exp");
    await testModel("gemini-2.5-flash-lite"); // The problematic one
}

run();
