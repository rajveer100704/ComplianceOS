import pytest
import httpx
from unittest.mock import patch, MagicMock
from fastapi import status

from main import app
from database.models.enums import IntegrationProvider, MembershipRole
from database.repositories.organization_repository import OrganizationRepository
from database.repositories.membership_repository import OrganizationMembershipRepository
from auth.dependencies import SecurityContext, get_security_context, get_db_session


@pytest.fixture
def mock_auth_user(db_session):
    """Creates test org, user, and security context."""
    from database.models.user import User

    async def _setup():
        org_repo = OrganizationRepository(db_session)
        org = await org_repo.create(
            name="Test Integration Org", slug="test-integration-org"
        )

        user = User(email="orgadmin@example.com", full_name="Org Admin")
        db_session.add(user)
        await db_session.flush()

        mem_repo = OrganizationMembershipRepository(db_session)
        membership = await mem_repo.create(
            organization_id=org.id, user_id=user.id, role=MembershipRole.ADMIN
        )

        context = SecurityContext(
            user=user,
            organization=org,
            membership=membership,
            permissions={"*"},
        )
        return org, user, context

    return _setup


@pytest.mark.asyncio
class TestIntegrationRouter:
    async def test_create_and_get_integration_api(self, db_session, mock_auth_user):
        org, user, context = await mock_auth_user()

        async def _override_db():
            yield db_session

        app.dependency_overrides[get_security_context] = lambda: context
        app.dependency_overrides[get_db_session] = _override_db

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            # 1. Create integration
            payload = {
                "provider": "slack",
                "name": "Production Slack Alerts",
                "secret": "https://hooks.slack.com/services/T00/B00/X00",
                "metadata": {"channel": "#compliance-alerts"},
                "is_active": True,
            }
            res = await client.post(
                f"/api/v1/organizations/{org.id}/integrations", json=payload
            )
            assert res.status_code == status.HTTP_201_CREATED
            data = res.json()
            assert data["provider"] == "slack"
            assert data["name"] == "Production Slack Alerts"
            assert data["credential_version"] == 1
            integration_id = data["id"]

            # 2. List integrations
            res_list = await client.get(f"/api/v1/organizations/{org.id}/integrations")
            assert res_list.status_code == status.HTTP_200_OK
            assert len(res_list.json()) == 1

            # 3. Get integration details & health
            res_health = await client.get(
                f"/api/v1/organizations/{org.id}/integrations/{integration_id}/health"
            )
            assert res_health.status_code == status.HTTP_200_OK
            assert res_health.json()["health_status"] == "healthy"

            with patch(
                "integrations.adapters.slack.SlackAdapter.execute",
                return_value=MagicMock(success=True, error_message=None),
            ):
                res_test = await client.post(
                    f"/api/v1/organizations/{org.id}/integrations/{integration_id}/test"
                )
                assert res_test.status_code == status.HTTP_200_OK
                assert res_test.json()["health_status"] == "healthy"

            # 5. Rotate secret credential
            res_rotate = await client.post(
                f"/api/v1/organizations/{org.id}/integrations/{integration_id}/rotate-secret",
                json={"new_secret": "https://hooks.slack.com/services/NEW/SECRET"},
            )
            assert res_rotate.status_code == status.HTTP_200_OK
            assert res_rotate.json()["credential_version"] == 2

        app.dependency_overrides.clear()
