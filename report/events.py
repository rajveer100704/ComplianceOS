import logging
from database.events import EventPublisher

logger = logging.getLogger("report_events")


class ReportEventPublisher:
    """Publishes domain events related to the compliance report workflows."""

    @staticmethod
    async def publish_report_generated(
        report_id: int, request_id: int, version: int, created_by: str
    ) -> None:
        """Publishes ReportGenerated domain event."""
        logger.info(f"Publishing ReportGenerated event for report {report_id}")
        await EventPublisher.publish_event(
            "ReportGenerated",
            {
                "report_id": report_id,
                "request_id": request_id,
                "version": version,
                "created_by": created_by,
            },
        )

    @staticmethod
    async def publish_report_approved(
        report_id: int, approved_by: str, timestamp: str
    ) -> None:
        """Publishes ReportApproved domain event."""
        logger.info(f"Publishing ReportApproved event for report {report_id}")
        await EventPublisher.publish_event(
            "ReportApproved",
            {
                "report_id": report_id,
                "approved_by": approved_by,
                "timestamp": timestamp,
            },
        )

    @staticmethod
    async def publish_report_published(
        report_id: int, published_by: str, timestamp: str
    ) -> None:
        """Publishes ReportPublished domain event."""
        logger.info(f"Publishing ReportPublished event for report {report_id}")
        await EventPublisher.publish_event(
            "ReportPublished",
            {
                "report_id": report_id,
                "published_by": published_by,
                "timestamp": timestamp,
            },
        )

    @staticmethod
    async def publish_report_archived(
        report_id: int, archived_by: str, timestamp: str
    ) -> None:
        """Publishes ReportArchived domain event."""
        logger.info(f"Publishing ReportArchived event for report {report_id}")
        await EventPublisher.publish_event(
            "ReportArchived",
            {
                "report_id": report_id,
                "archived_by": archived_by,
                "timestamp": timestamp,
            },
        )

    @staticmethod
    async def publish_report_exported(
        report_id: int, format_str: str, exported_by: str, timestamp: str
    ) -> None:
        """Publishes ReportExported domain event."""
        logger.info(
            f"Publishing ReportExported event for report {report_id} to format {format_str}"
        )
        await EventPublisher.publish_event(
            "ReportExported",
            {
                "report_id": report_id,
                "format": format_str,
                "exported_by": exported_by,
                "timestamp": timestamp,
            },
        )
