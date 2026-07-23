from observability.sentry import set_sentry_context, setup_sentry


def test_sentry_context_setting():
    """Test set_sentry_context executes safely without raising exceptions."""
    set_sentry_context(
        user_id="usr_123",
        organization_id="org_456",
        role="ADMIN",
        request_id="req_789",
    )


def test_setup_sentry_none_dsn():
    """Test setup_sentry returns False when DSN is None."""
    assert setup_sentry(dsn=None) is False
