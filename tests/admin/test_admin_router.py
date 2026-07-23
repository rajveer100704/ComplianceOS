"""Integration tests for Admin REST API endpoints (Policies, Audit Logs, Worker Queue)."""

import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from database.repositories.organization_repository import OrganizationRepository
from database.repositories.membership_repository import OrganizationMembershipRepository
from auth.repositories.user_repository import UserRepository
from auth.dependencies import get_db_session
from database.models.enums import MembershipRole
from auth.services.jwt_service import JWTService


@pytest.mark.asyncio
async def test_admin_policies_and_audit_api(db_session):
    """Test policy creation, simulation, and audit export API endpoints."""
    user_repo = UserRepository(db_session)
    org_repo = OrganizationRepository(db_session)
    member_repo = OrganizationMembershipRepository(db_session)

    user = await user_repo.create_google_user(
        email="admin_policy@complianceos.com",
        provider_user_id="google-admin-101",
        full_name="Admin Policy User",
    )

    org = await org_repo.create(
        name="Governance Org",
        slug="gov-org",
    )

    await member_repo.create(
        user_id=user.id,
        organization_id=org.id,
        role=MembershipRole.OWNER,
    )
    await db_session.flush()

    jwt_svc = JWTService()
    token = jwt_svc.generate_access_token(
        user_id=user.id,
        email=user.email,
        role="owner",
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-Id": org.id,
    }

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # 1. Create policy
            policy_payload = {
                "name": "High Risk Approval Gate",
                "description": "Block approval if risk score > 80",
                "trigger_event": "claim.approved",
                "priority": 10,
                "expression": "risk_score > 80",
                "rules": [
                    {
                        "rule_type": "APPROVAL_GATE",
                        "error_message": "Cannot approve high-risk claims without dual review",
                    }
                ],
            }

            res_create = await client.post(
                f"/api/v1/organizations/{org.id}/admin/policies",
                json=policy_payload,
                headers=headers,
            )
            assert res_create.status_code == 201
            data = res_create.json()
            assert data["name"] == "High Risk Approval Gate"
            assert data["trigger_event"] == "claim.approved"

            # 2. Simulate policy
            sim_payload = {"expression": "risk_score > 70 AND status == UNSUPPORTED"}
            res_sim = await client.post(
                f"/api/v1/organizations/{org.id}/admin/policies/simulate",
                json=sim_payload,
                headers=headers,
            )
            assert res_sim.status_code == 200
            sim_data = res_sim.json()
            assert sim_data["total_evaluated"] == 3

            # 3. Query audit logs
            res_audit = await client.get(
                f"/api/v1/organizations/{org.id}/admin/audit-logs",
                headers=headers,
            )
            assert res_audit.status_code == 200
            assert isinstance(res_audit.json(), list)

            # 4. Export audit logs CSV
            res_export = await client.get(
                f"/api/v1/organizations/{org.id}/admin/audit-logs/export?format=csv",
                headers=headers,
            )
            assert res_export.status_code == 200
            assert "text/csv" in res_export.headers["content-type"]

            # 5. Worker queue status
            res_workers = await client.get(
                f"/api/v1/organizations/{org.id}/admin/workers/queue",
                headers=headers,
            )
            assert res_workers.status_code == 200
            assert res_workers.json()["status"] == "healthy"
    finally:
        app.dependency_overrides.pop(get_db_session, None)
