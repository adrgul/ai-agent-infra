// Node.js example — loads `apikulcs.env` (if present) and calls OpenAI Chat Completions.
// Requirements: Node 18+ (global `fetch`) or install a fetch polyfill.
// Usage: from this folder run `node api_example.js` (or `npm start` after `npm install`)

const fs = require("fs");
const path = require("path");

function loadEnvFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) return;
    const content = fs.readFileSync(filePath, "utf8");
    content.split(/\r?\n/).forEach(line => {
      line = line.trim();
      if (!line || line.startsWith("#")) return;
      const eq = line.indexOf("=");
      if (eq === -1) return;
      let key = line.slice(0, eq).trim();
      let val = line.slice(eq + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (!process.env[key]) process.env[key] = val;
    });
  } catch (err) {
    console.warn("Could not load env file:", err.message || err);
  }
}

// Try to load local apikulcs.env in the same folder
loadEnvFile(path.join(__dirname, "apikulcs.env"));

const API_KEY = process.env.OPENAI_API_KEY || process.env.API_TOKEN || "";
const API_URL = process.env.API_URL || "https://api.openai.com/v1/chat/completions";

async function ensureFetch() {
  if (typeof fetch !== "undefined") return fetch;
  try {
    // Try to require node-fetch v2 as a fallback (works with CommonJS)
    // If not installed, this will throw and user must run `npm install` or use Node 18+.
    // eslint-disable-next-line global-require
    const nf = require("node-fetch");
    return nf;
  } catch (e) {
    throw new Error("No global fetch available. Use Node 18+ or install node-fetch: npm install node-fetch@2");
  }
}

async function callOpenAI(prompt = "Hello from csorsz.adam example") {
  if (!API_KEY) throw new Error("OPENAI_API_KEY not set in environment or apikulcs.env");
  const fetchFn = await ensureFetch();
  const body = {
    model: process.env.OPENAI_MODEL || "gpt-3.5-turbo",
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: prompt }
    ],
    max_tokens: 200
  };

  const res = await fetchFn(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${API_KEY}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`OpenAI HTTP ${res.status}: ${txt}`);
  }
  return res.json();
}

if (require.main === module) {
  const prompt = process.argv.slice(2).join(" ") || "Kezdj egy rövid bemutatkozással magyarul.";
  callOpenAI(prompt).then(r => {
    try {
      // Chat completion response format: extract assistant message
      const msg = r.choices && r.choices[0] && r.choices[0].message && r.choices[0].message.content;
      if (msg) console.log(msg);
      else console.log(JSON.stringify(r, null, 2));
    } catch (e) {
      console.log(JSON.stringify(r, null, 2));
    }
  }).catch(err => {
    console.error("Error:", err.message || err);
  });
}
