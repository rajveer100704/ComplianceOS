# Contributing to ComplianceOS

Thank you for your interest in contributing to ComplianceOS!

---

## Local Development Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/rajveer100704/CompliaceOS.git
   cd ComplianceOS
   ```

2. **Set Up Python Virtual Environment**:
   ```bash
   python -m venv venv
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Launch Local Infrastructure**:
   ```bash
   docker compose up -d
   ```

5. **Execute Migrations & Run Server**:
   ```bash
   python -m alembic upgrade head
   python main.py
   ```
   Open `http://localhost:8000` to access the Review Workstation UI.

6. **Run Automated Tests**:
   ```bash
   python -m pytest test_main.py
   ```

---

## Code Quality Guidelines

- **Style**: Follow PEP 8 guidelines.
- **Formatting**: Run `black .` and `ruff check .`.
- **Type Checking**: Verify with `mypy --ignore-missing-imports .`.
- **Pull Requests**: Submit PRs against the `main` branch with descriptive summaries.
