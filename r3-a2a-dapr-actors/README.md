# 🛰️ Recipe 3 – A2A + Agents SDK + Dapr Actors (EDA Style)

This recipe upgrades the baseline R2 by introducing **Dapr Actors** for Multi User Horizontal Scalable Agentic Systems.  

---

## ⚡ Philosophy

- **Why Dapr?** → PubSub abstraction (Redis, Kafka, RabbitMQ, etc.) + service discovery.  
- **Why split containers?** → Decouple web/BFF logic from agent execution.  
- **Still simple** → Just two containers + sidecars, runs fine on local K8 cluster and deploy anywhere or BareMetal or Managed service.  

---

## 🏗️ Architecture

```

+-------------------+             +------------------+
\|   A2A + BFF       |             |    Dapr Actor    |
\|  (FastAPI + SDK)  |             |     |
\|                   |             |                  |
\|  \[Dapr Sidecar]   | <---------> |  \[Dapr Sidecar] |
+-------------------+             +------------------+
\|                               |
v                               v
Pub/Sub <------ Redis/Kafka ------> Pub/Sub

```

👉 Back to main doc: [Infinite Agent Streams README](../readme.md)  