const fs = require("fs");
const path = require("path");

const RULES_PATH = path.join(__dirname, "..", "..", "config", "keywords.json");

function loadRules() {
  const raw = fs.readFileSync(RULES_PATH, "utf-8");
  return JSON.parse(raw);
}

function findReply(commentText) {
  const { rules, defaultReply } = loadRules();
  const text = (commentText || "").toLowerCase();

  for (const rule of rules) {
    const hit = rule.keywords.some((keyword) =>
      text.includes(keyword.toLowerCase())
    );
    if (hit) return rule.reply;
  }

  return defaultReply || null;
}

module.exports = { findReply };
