---
name: integrations
description: >
  Use when implementing enterprise integrations: Slack notifications, Jira issue creation,
  GitHub Issues sync, S3/Cloudflare R2 object storage, Microsoft Teams webhooks.
  Covers retry policies, webhook signing, circuit breakers, and idempotency.
---

# Enterprise Integrations Skill

## When to Use

- Implementing Slack, Teams, Jira, or GitHub connectors.
- Adding S3 or Cloudflare R2 file storage.
- Implementing webhook delivery and retry.
- Adding circuit breaker patterns for external APIs.

## Integration Architecture

```
Domain Event (e.g., "claim_approved")
       │
       ▼
Outbox Table (within business transaction)
       │
       ▼
Worker Dispatcher (polls outbox)
       │
       ├── Slack Adapter → POST webhook URL
       ├── Jira Adapter → POST /rest/api/3/issue
       ├── GitHub Adapter → POST /repos/.../issues
       ├── S3 Adapter → PUT presigned URL
       └── Teams Adapter → POST webhook URL
```

## Connector Patterns

### Retry Policy
- Exponential backoff: `delay = base * 2^attempt` (base=1s, max=60s).
- Maximum 5 retries per event.
- After max retries → mark as `failed`, alert.

### Webhook Signing
- Sign outgoing webhooks with HMAC-SHA256.
- Include `X-Signature-256` header.
- Verify incoming webhooks by recomputing signature.

### Circuit Breaker
- Track failure count per integration.
- Open circuit after 5 consecutive failures.
- Half-open after 60 seconds (allow single probe request).
- Close circuit on successful probe.

### Idempotency
- Generate idempotency key per event: `SHA-256(event_id + integration_id)`.
- Check if event was already delivered before sending.
- Store delivery receipts with timestamps.

## Connector Specifications

### Slack
- Incoming webhook URL stored encrypted.
- Payload: Blocks Kit JSON.
- Triggers: claim_approved, claim_rejected, report_generated, snapshot_created.

### Jira
- OAuth2 or API token authentication.
- Create issues on non-compliant claims.
- Map claim fields to Jira issue fields.
- Sync status changes bidirectionally (optional).

### GitHub Issues
- GitHub App or Personal Access Token.
- Create issues for unresolved claims.
- Label with regulation type and risk level.

### S3 / Cloudflare R2
- Generate presigned upload URLs (5-minute expiry).
- Store reports and document exports.
- Organize by: `/{org_id}/{project_id}/{report_id}/`.

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) §4 (Event Bus)
- [PERFORMANCE.md](../../PERFORMANCE.md) §2 (Async & Concurrency)
