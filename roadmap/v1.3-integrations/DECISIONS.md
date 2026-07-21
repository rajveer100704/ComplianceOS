# Architectural Decisions Log — Version 1.3: Enterprise Integrations & Connectors

- **Decision 1**: Webhook signing with HMAC-SHA256 for all outbound events.
- **Decision 2**: Asynchronous outbox worker handling to isolate API latency from user HTTP requests.
