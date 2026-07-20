# ComplianceOS — Operational Validation & Verification Runbook

**Document Purpose:** Runbook and execution protocol for recording empirical runtime evidence during live staging or production deployment validation.

---

## 1. Operational Verification Policy & Status Taxonomy

All findings in this validation log must strictly adhere to the following taxonomy:

- **EXECUTED AND PASSED**: Quoted live HTTP response headers, terminal execution output, database query results, or worker logs from a live deployment.
- **EXECUTED AND FAILED**: Terminal execution output or error stack trace demonstrating runtime failure.
- **NOT EXECUTED**: Live deployment has not been performed; operational evidence pending.

---

## 2. Standardized Test Dataset

To ensure reproducible operational validation, execute the runbook using the following synthetic aerospace compliance dataset:

- **Regulatory Corpus**: `FAA_Part450_FlightSafety.txt` (14 CFR 450.115 Flight Safety Analysis requirements).
- **Engineering Specification**: `System_Requirements_Spec.txt` (Thermal protection, dual-redundant watchdog timers).
- **Hazard Analysis**: `Hazard_Analysis_Report.txt` (Public casualty risk calculations < 1e-4).
- **Verification Test Procedure**: `Verification_Test_Procedure.txt` (Pressure vessel burst testing standards).

---

## 3. Evidence Collection Protocol

For every completed phase, attach the following evidence artifacts to convert status from `NOT EXECUTED` to `EXECUTED AND PASSED`:

- **curl Command**: Exact CLI request executed.
- **HTTP Status & Headers**: Status code and `X-Request-ID` header.
- **JSON Response Body**: Complete or sanitized JSON payload returned by API.
- **Server/Worker Logs**: Terminal output or CloudWatch/Grafana log lines.
- **Database Query Result**: SQL verification query confirming persisted record.

---

## 4. Phase-by-Phase Live Validation Log

### Step 1: Health Liveness Probe (`GET /healthz`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -i https://api.complianceos.yourdomain.com/healthz`
- **Expected Status:** HTTP `200 OK`
- **Expected Headers:** `X-Request-ID`, `X-Content-Type-Options: nosniff`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 2: Subsystem Readiness Probe (`GET /readyz`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -i https://api.complianceos.yourdomain.com/readyz`
- **Expected Status:** HTTP `200 OK`
- **Expected Payload:**
  ```json
  {
    "status": "ready",
    "checks": {
      "database": "connected",
      "qdrant": "ready",
      "worker_queue": "ready",
      "embeddings": "loaded"
    }
  }
  ```
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 3: Create Compliance Request (`POST /api/requests`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -X POST https://api.complianceos.yourdomain.com/api/requests -H "Content-Type: application/json" -d '{"project": "Satellite Safety", "regulator": "FAA Part 450", "owner": "John Smith"}'`
- **Expected Status:** HTTP `200 OK`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 4: Upload Document (`POST /api/requests/{id}/documents`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -X POST https://api.complianceos.yourdomain.com/api/requests/{id}/documents ...`
- **Expected Status:** HTTP `200 OK`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 5: Execute Verification Pipeline (`POST /api/requests/{id}/run`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -X POST https://api.complianceos.yourdomain.com/api/requests/{id}/run`
- **Expected Status:** HTTP `200 OK`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 6: Reviewer Assignment & Snapshot (`POST /api/requests/{id}/snapshots`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -X POST https://api.complianceos.yourdomain.com/api/requests/{id}/snapshots ...`
- **Expected Status:** HTTP `200 OK`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 7: Report Generation & Stepper Transition (`POST /api/reports/{id}/transition`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -X POST https://api.complianceos.yourdomain.com/api/reports/{id}/transition ...`
- **Expected Status:** HTTP `200 OK`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

### Step 8: Asynchronous Document Export (`POST /api/reports/{id}/export`)
- **Status:** `NOT EXECUTED`
- **Verification Method:** `curl -X POST https://api.complianceos.yourdomain.com/api/reports/{id}/export ...`
- **Expected Status:** HTTP `200 OK`
- **Evidence Log (Pending Live Deployment):**
  ```
  [Paste raw HTTP response here upon execution]
  ```

---

## 5. Operational Evidence Checklist

| Operational Capability | Status | Evidence Collected |
| :--- | :--- | :--- |
| **Server Startup & Migration Logs** | `NOT EXECUTED` | Pending deployment |
| **OpenAPI Interface (/docs)** | `NOT EXECUTED` | Pending deployment |
| **Prometheus Telemetry (/metrics)** | `NOT EXECUTED` | Pending deployment |
| **PostgreSQL Connection & Schema State** | `NOT EXECUTED` | Pending deployment |
| **Qdrant Vector Collection Indexing** | `NOT EXECUTED` | Pending deployment |
| **Async Task Runner Execution Logs** | `NOT EXECUTED` | Pending deployment |
| **Review Workstation UI Operations** | `NOT EXECUTED` | Pending deployment |

---

## 6. Operational Readiness Verdict

- **Repository Audit Status:** Complete (Static architecture & code inspection verified)
- **Live Deployment Status:** Pending execution against production cloud target
- **Certification State:** Pending population of empirical runtime validation logs above
