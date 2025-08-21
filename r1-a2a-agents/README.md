# 🍲 Recipe 1: All-in-One Agent Stack (No-Cost MVP)

This recipe runs everything in **one container + one FastAPI server** — keeping things **simple and cost-free**.
Perfect if you **don’t know Kubernetes yet** or want to deploy on **serverless containers** (Fly.io, Railway, Render, etc.).

---

## 🧩 Components (all-in-one)

* **A2A Server** → Agent-to-Agent protocol server for agent communication
* **BFF (Backend-for-Frontend)** → Handles client API requests, streaming responses
* **Agent(s)** → Your AI agent logic (calls OpenAI, Claude, Gemini, Grok, etc.)

All three live in **the same container + server**.
⚡ No extra infra required.

---

## 🖼️ Architecture (ASCII)

```
+--------------------------------------+
|         🚀 Single Container           |
|                                      |
|  +-----------+   +-------------+     |
|  |   A2A     |   |     BFF     |     |
|  |  Server   |<->|   (API)     |     |
|  +-----------+   +-------------+     |
|          \             |             |
|           \            |             |
|            \           v             |
|          +------------------+        |
|          |   AI Agent(s)    |        |
|          |  (OpenAI, etc.)  |        |
|          +------------------+        |
|                                      |
+--------------------------------------+
```

---

## 🚀 Run the Stack

1. Clone repo and set up environment:

   ```bash
   cd r1-a2a-agents
   cp .env.example .env   # update keys
   ```

2. Start the unified server:

   ```bash
   uv run main.py
   ```

3. (Optional) Run the **A2A Inspector** for debugging:

   ```bash
   cd a2a-inspector
   chmod +x run.sh
   ./run.sh
   ```

---

## ✅ Why this approach?

* **Zero-cost MVP** → great for prototyping and hackathons
* **Single container** → easier to deploy without Kubernetes
* **Serverless friendly** → works on Fly.io, Railway, Render, or even Docker run

---
