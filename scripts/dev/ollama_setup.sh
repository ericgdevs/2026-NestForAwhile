#!/bin/sh
set -eu

MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
command -v ollama >/dev/null 2>&1 || {
  echo "Ollama is required. Install it from https://ollama.com/download." >&2
  exit 1
}
ollama pull "$MODEL"
echo "Pulled Ollama model: $MODEL"
