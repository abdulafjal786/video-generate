"""Optional LLM script writer.

backend "auto" tries, in order:
  - an OpenAI-compatible API if llm.api_key (or OPENAI_API_KEY / GEMINI_API_KEY) is set
  - Ollama running locally (http://127.0.0.1:11434)
backend "none" disables the LLM and uses the built-in planner.
"""
import json
import os
import re

import requests

GEMINI_OPENAI = "https://generativelanguage.googleapis.com/v1beta/openai"


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if m:
            return json.loads(m.group(0))
        raise


def _openai(system, user, base, key, model, timeout):
    r = requests.post(base.rstrip("/") + "/chat/completions", timeout=timeout,
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json={"model": model, "temperature": 0.8,
                            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    r.raise_for_status()
    return _extract_json(r.json()["choices"][0]["message"]["content"])


def _ollama(system, user, url, model, timeout):
    if not model:
        tags = requests.get(url + "/api/tags", timeout=3).json().get("models", [])
        if not tags:
            raise RuntimeError("Ollama has no models; run: ollama pull llama3.2")
        model = tags[0]["name"]
    r = requests.post(url + "/api/chat", timeout=timeout, json={
        "model": model, "stream": False, "format": "json",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    r.raise_for_status()
    return _extract_json(r.json()["message"]["content"])


def complete_json(system, user, lcfg, log=print):
    backend = lcfg.get("backend", "auto")
    timeout = float(lcfg.get("timeout", 180))
    key = lcfg.get("api_key") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    base = lcfg.get("base_url") or ("https://api.openai.com/v1" if os.environ.get("OPENAI_API_KEY") and not lcfg.get("api_key") else "")
    if not base and (lcfg.get("api_key") or os.environ.get("GEMINI_API_KEY")):
        base = GEMINI_OPENAI
    if backend in ("auto", "openai") and key and base:
        model = lcfg.get("model") or ("gemini-2.5-flash" if "googleapis" in base else "gpt-4o-mini")
        out = _openai(system, user, base, key, model, timeout)
        out["_backend"] = model
        return out
    if backend in ("auto", "ollama"):
        url = (lcfg.get("ollama_url") or "http://127.0.0.1:11434").rstrip("/")
        try:
            requests.get(url + "/api/tags", timeout=2)
        except Exception:
            if backend == "ollama":
                raise RuntimeError("Ollama is not running at " + url)
            return None
        out = _ollama(system, user, url, lcfg.get("ollama_model"), timeout)
        out["_backend"] = "ollama"
        return out
    return None
