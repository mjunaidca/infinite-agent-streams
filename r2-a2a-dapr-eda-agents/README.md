# 🛰️ Recipe 2 – A2A + Agents SDK + Dapr PubSub (EDA Style)

This recipe upgrades the baseline R1 by introducing **Dapr** for Pub/Sub messaging and sidecar-based service discovery.  

It separates the **A2A+BFF layer** from the **Agent runtime**, enabling **independent scaling** and **event-driven async streaming**. This is perfect for long running tasks where you can use A2A Push Notifications with current architecture.

---

## ⚡ Philosophy

- **Why Dapr?** → PubSub abstraction (Redis, Kafka, RabbitMQ, etc.) + service discovery.  
- **Why split containers?** → Decouple web/BFF logic from agent execution.  
- **Still simple** → Just two containers + sidecars, runs fine on local K8 cluster and deploy anywhere or BareMetal or Managed service.  

---

## 🏗️ Architecture

```

+-------------------+             +------------------+
\|   A2A + BFF       |             |    Agent         |
\|  (FastAPI + SDK)  |             |     |
\|                   |             |                  |
\|  \[Dapr Sidecar]   | <---------> |  \[Dapr Sidecar]  |
+-------------------+             +------------------+
\|                               |
v                               v
Pub/Sub <------ Redis/Kafka ------> Pub/Sub

```

**Flow:**  
1. Frontend calls BFF → A2A.  
2. A2A publishes messages into Dapr PubSub.  
3. Agent subscribes and processes events.  
4. Agent publishes results back → A2A → frontend SSE.  

---

## 🚀 Components

- **Container 1:**  
  - A2A protocol server  
  - BFF (API bridge)  
  - Dapr sidecar  

- **Container 2:**  
  - Agent runtime (AgentExecutor from OpenAI Agents SDK)  
  - Dapr sidecar  

---

## 📦 When to Use

✅ When you want:  
- Pub/Sub abstraction without managing Kafka/Rabbit directly.  
- Agents and API layer scaling separately.  
- Same dev simplicity as R1, but closer to Kubernetes-native infra.  

❌ Skip if:  
- You just need a quick ping-pong demo (use R1).  
- You don’t want to run extra sidecars or EDA (Redis/Dapr).  

---

👉 Back to main doc: [Infinite Agent Streams README](../readme.md)  