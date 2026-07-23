import pytest
from observability.tracing import trace_span, get_tracer


@pytest.mark.asyncio
async def test_trace_span_decorator():
    """Test trace_span decorator executes function cleanly without exception."""

    @trace_span("test_custom_span")
    async def sample_async_func():
        return "success"

    res = await sample_async_func()
    assert res == "success"
