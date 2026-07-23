# ADR 0009: Policy Engine & Enterprise Governance Platform Architecture

## Date: 2026-07-23
## Status: Accepted

## Context

As ComplianceOS scales into multi-tenant enterprise RAG regulatory compliance, organizations require granular governance over claim verification, approval workflows, evidence requirements, and auditability. Hardcoding compliance rules inside router or service code creates technical debt, prevents custom compliance frameworks (e.g. FAA Part 450, NRC 10 CFR, ASME BPVC, SOC2), and lacks audit traceability.

## Key Architectural Decisions

1. **Immutable Policy Versioning (`Policy` + `PolicyVersion`)**:
   Policies are never overwritten in-place. Updating or rolling back a policy creates a new `PolicyVersion` record with a SHA-256 checksum. Audit logs reference exact `policy_version_id` for complete historical reproducibility.

2. **System Templates vs Organization Instances (`SystemPolicyPack` → `OrganizationPolicyPack`)**:
   Global regulatory frameworks are published as immutable `SystemPolicyPackModel` templates (e.g., FAA Part 450, SOC2). When a tenant installs a pack, an `OrganizationPolicyPackModel` instance creates tenant-owned editable policy copies.

3. **Compiler → Validator → Cache Evaluation Pipeline**:
   Human-readable condition expressions (e.g., `risk_score > 80 AND count(pinned_evidence) < 1`) pass through a structured compilation pipeline (`PolicyCompiler`), semantic AST validator (`PolicyValidator`), and SHA-256 in-memory cache (`PolicyCompilerCache`).

4. **Structured Decision Output with Explainable `EvaluationTrace`**:
   The policy engine returns a rich `PolicyDecision` object containing an `EvaluationTrace` detailing why rules `PASSED`, `FAILED`, or were `SKIPPED`.

5. **DAG Workflow Engine with Action Plugin Architecture (`workflow/`)**:
   Post-approval actions are executed as Directed Acyclic Graphs (`WorkflowDAG`) using pluggable action handlers (`BaseWorkflowAction`). Every action configures a `RetryPolicy` (`NONE`, `LINEAR`, `EXPONENTIAL`, `EXPONENTIAL_JITTER`) and logs runtime history (`WorkflowExecutionModel`, `WorkflowStepExecutionModel`).

6. **Dry-Run & Simulation Execution Modes**:
   - `PolicySimulator`: Evaluates draft rules against historical claim batches before activation (`Blocked`, `Allowed`, `Escalated`).
   - Workflow `dry_run=True`: Previews action consequences without mutating production databases or firing external webhooks.

7. **Generic `StateMachine[T]`**:
   State transitions follow a type-generic state machine reusable across `Claim`, `Report`, `Evidence`, and `Document` (`Draft → Pending Review → Pending Approval → Approved → Published`).

## Consequences

- **Positive**: Complete audit compliance, zero circular import cascades, extensible action plugins, explainable decision traces, zero-downtime policy updates, and zero risk of cross-tenant policy contamination.
- **Trade-offs**: Requires database schema for policy versioning, AST caching, and step execution logging.
