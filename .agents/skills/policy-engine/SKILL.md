---
name: policy-engine
description: >
  Use when implementing the compliance policy engine: configurable approval rules,
  automatic risk escalation, approval gates, workflow event automation, and
  scheduled compliance jobs.
---

# Policy Engine Skill

## When to Use

- Implementing configurable approval rules.
- Adding automatic escalation for high-risk claims.
- Creating approval gates that block report publication.
- Implementing post-approval workflow automation.
- Adding scheduled compliance checks.

## Policy Engine Architecture

```
Policy Definition (YAML/JSON)
       │
       ▼
Rule Engine (evaluates conditions)
       │
       ├── Approval Gates (block/allow actions)
       ├── Escalation Triggers (notify/assign)
       └── Workflow Triggers (automate sequences)
              │
              ▼
       Workflow Executor
       ├── Step 1: Generate PDF
       ├── Step 2: Upload to S3
       ├── Step 3: Create Jira ticket
       ├── Step 4: Send Slack notification
       └── Step 5: Email reviewer
```

## Policy Definition Format

```yaml
policies:
  - name: dual_approval_for_critical
    description: Require two reviewers for high-risk claims
    trigger: claim.risk_level == "critical"
    rules:
      - type: approval_gate
        condition: count(approvals) >= 2
        action: block_until_met
        message: "Critical claims require dual approval"

  - name: evidence_required
    description: Block approval without evidence
    trigger: claim.decision == "approve"
    rules:
      - type: approval_gate
        condition: count(pinned_evidence) >= 1
        action: block_until_met
        message: "Cannot approve without pinned evidence"

  - name: escalate_unsupported
    description: Escalate unsupported claims to lead reviewer
    trigger: claim.verdict == "UNSUPPORTED" and claim.confidence < 0.3
    rules:
      - type: escalation
        assign_to: lead_reviewer
        priority: high
        notify: [slack, email]
```

## Rule Types

| Type | Purpose | Example |
| :--- | :--- | :--- |
| `approval_gate` | Block action until condition is met | Require 2 approvals for critical claims |
| `escalation` | Assign to higher authority | Route unsupported claims to lead |
| `notification` | Alert stakeholders | Slack message when report published |
| `workflow` | Trigger automated sequence | PDF → S3 → Jira → Slack after approval |
| `validation` | Check data quality | Reject claims shorter than 20 characters |
| `schedule` | Periodic compliance check | Weekly audit of unresolved claims |

## Workflow Execution

```python
class WorkflowExecutor:
    async def execute(self, workflow: Workflow, context: dict):
        for step in workflow.steps:
            try:
                result = await self.run_step(step, context)
                context[step.name] = result
            except StepError as e:
                if step.on_failure == "halt":
                    raise WorkflowHaltedError(step, e)
                elif step.on_failure == "skip":
                    logger.warning(f"Step {step.name} failed, skipping")
                    continue
```

## References

- [ARCHITECTURE.md](../../ARCHITECTURE.md) §4 (Event Bus)
- [CODING_STANDARD.md](../../CODING_STANDARD.md) §6 (Service Layer)
