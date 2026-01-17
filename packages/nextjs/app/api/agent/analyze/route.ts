import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");
const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash-lite" });

const SYSTEM_PROMPT = `
You are the brain of an autonomous crypto agent called MIAA (Monad Intent-Arbitrage Agent).
Your job is to parse natural language user intents into structured JSON execution plans.

Supported Actions:
1. SWAP: User wants to trade tokens.
2. ARBITRAGE: User wants to run arbitrage strategies on specific pairs or the market.

Output JSON format ONLY. Do NOT use markdown code blocks. Do NOT include any text outside the JSON.

--- CASE 1: SWAP ---
User: "Swap 50 MON to USDT"
Output:
{
  "intent": "SWAP",
  "confidence": 0.99,
  "params": {
    "tokenIn": "MON",
    "tokenOut": "USDT",
    "amount": 50
  },
  "thought": "User wants to swap exact amount."
}

--- CASE 2: ARBITRAGE (MARKET) ---
User: "Start aggressive arbitrage on all pools"
Output:
{
  "intent": "ARBITRAGE",
  "confidence": 0.95,
  "params": {
    "strategy": "AGGRESSIVE",
    "token": "MARKET",
    "mode": "all"
  },
  "thought": "User requested aggressive arbitrage strategy."
}

--- CASE 3: ARBITRAGE (SPECIFIC PAIR) ---
User: "Check MON/USDC for arbitrage" or "Is there arb on MON/CHOG?"
Output:
{
  "intent": "ARBITRAGE",
  "confidence": 0.98,
  "params": {
    "token": "MON/USDC",
    "mode": "manual"
  },
  "thought": "User wants to check specific pair for arbitrage."
}

--- CASE 4: ANALYZE ---
User: "How is the market?"
Output:
{
  "intent": "ANALYZE",
  "confidence": 0.9,
  "params": { "metric": "VOLATILITY" },
  "thought": "User asked for general market analysis."
}
`;

export async function POST(req: Request) {
  try {
    const { instruction } = await req.json();

    console.log("[API] Received instruction:", instruction);
    console.log("[API] Key present?", !!process.env.GEMINI_API_KEY);

    if (!process.env.GEMINI_API_KEY) {
      return NextResponse.json(
        { error: "Missing GEMINI_API_KEY in server env" },
        { status: 500 }
      );
    }

    const result = await model.generateContent([
      SYSTEM_PROMPT,
      `User input: "${instruction}"`
    ]);

    const response = result.response;
    const text = response.text();
    console.log("[API] Gemini Raw Output:", text);

    // Clean markdown code blocks if present
    const cleanJson = text.replace(/```json/g, "").replace(/```/g, "").trim();

    const parsed = JSON.parse(cleanJson);
    return NextResponse.json(parsed);

  } catch (error) {
    console.error("Gemini API Error:", error);
    return NextResponse.json(
      { error: "Failed to parse intent", details: String(error) },
      { status: 500 }
    );
  }
}
