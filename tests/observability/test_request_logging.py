import json
import logging
from observability.logging import JSONLogFormatter


def test_json_log_formatter_correlation_fields():
    """Test JSONLogFormatter output includes request and correlation fields."""
    formatter = JSONLogFormatter()
    logger = logging.getLogger("test_logger")
    record = logger.makeRecord(
        name="test_logger",
        level=logging.INFO,
        fn="test_fn",
        lno=10,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    setattr(record, "request_id", "req-123")
    setattr(record, "organization_id", "org-456")
    setattr(record, "user_id", "usr-789")
    setattr(record, "latency_ms", 12.34)

    output = formatter.format(record)
    log_json = json.loads(output)

    assert log_json["message"] == "Test log message"
    assert log_json["request_id"] == "req-123"
    assert log_json["organization_id"] == "org-456"
    assert log_json["user_id"] == "usr-789"
    assert log_json["latency_ms"] == 12.34
