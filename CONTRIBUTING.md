# Contributing to ComplianceOS

Thank you for your interest in contributing to **ComplianceOS** — an enterprise AI regulatory compliance verification platform.

---

## 🏗 Architecture Principles & Constraints

All contributions must strictly follow our layered architecture (`AGENTS.md` & `ARCHITECTURE.md`):

1. **Layer Hierarchy**: `Router -> Service -> Repository -> ORM/Qdrant`. Never skip layers.
2. **Ports & Adapters**: Subsystem abstractions (`RetrieverPort`, `MemoryStorePort`, `GraphProviderPort`) must use dependency injection.
3. **Execution Context**: All public service signatures accept `ExecutionContext` carrying trace IDs and token budgets.
4. **Evidence Models**: Use standard domain models (`Evidence`, `Citation`, `Provenance`, `EvidenceBundle`) instead of loose dictionaries.

---

## 🛠 Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/rajveer100704/ComplianceOS.git
cd ComplianceOS

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate RSA security keys
python scripts/generate_dev_keys.py

# 5. Run test suite
python -m pytest test_main.py tests/ -q
```

---

## 🧪 Quality Gates

Before submitting a Pull Request, run the local quality checks:

```bash
# Code Formatting
black --check .

# Linting
ruff check .

# Automated Tests
pytest test_main.py tests/
```
