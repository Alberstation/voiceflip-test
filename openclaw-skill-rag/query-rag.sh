#!/usr/bin/env bash
# Query VoiceFlip RAG API. Usage: query-rag.sh "Your question here"
# Requires RAG_API_URL (default http://app:8000) and curl.

set -e
RAG_API_URL="${RAG_API_URL:-http://app:8000}"
QUESTION="${1:-}"
if [ -z "$QUESTION" ]; then
  echo "Usage: query-rag.sh \"Your question here\""
  exit 1
fi
# Optional: use mmr for diversity (second arg)
TECHNIQUE="${2:-top_k}"
# Escape double quotes in question for JSON
Q_ESC=$(echo "$QUESTION" | sed 's/\\/\\\\/g; s/"/\\"/g')
BODY="{\"question\": \"$Q_ESC\", \"retrieval_technique\": \"$TECHNIQUE\"}"
RESP=$(curl -sS -X POST "${RAG_API_URL}/query" \
  -H "Content-Type: application/json" \
  -d "$BODY")
# Extract "answer": "..." (portable, no jq)
if echo "$RESP" | grep -q '"answer"'; then
  echo "$RESP" | sed -n 's/.*"answer"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | sed 's/\\n/\n/g'
else
  echo "$RESP"
fi
