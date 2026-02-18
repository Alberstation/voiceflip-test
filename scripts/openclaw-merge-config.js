#!/usr/bin/env node
/**
 * Merges candidate-friendly defaults into OpenClaw config on gateway startup.
 * - allowInsecureAuth: true — enables token-only auth, skips device pairing (local/dev)
 * - tools.allow: ["sessions_send"] — lets the frontend proxy send messages
 * Used for the technical test: no Browser Relay, Control UI, or pairing setup needed.
 */
const fs = require("fs");
const path = require("path");

const configPath = path.join(
  process.env.HOME || "/home/node",
  ".openclaw",
  "openclaw.json"
);

try {
  if (!fs.existsSync(configPath)) return;
  const raw = fs.readFileSync(configPath, "utf8");
  const config = JSON.parse(raw);

  config.gateway = config.gateway || {};
  config.gateway.controlUi = config.gateway.controlUi || {};
  config.gateway.controlUi.allowInsecureAuth = true;
  config.gateway.tools = config.gateway.tools || {};
  const allow = config.gateway.tools.allow;
  config.gateway.tools.allow = Array.isArray(allow)
    ? allow.includes("sessions_send")
      ? allow
      : [...allow, "sessions_send"]
    : ["sessions_send"];

  fs.writeFileSync(configPath, JSON.stringify(config, null, 2), "utf8");
} catch (e) {
  // Non-fatal; gateway will start with existing config
  if (process.env.DEBUG) console.error("openclaw-merge-config:", e.message);
}
