import re
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class DeviceInfoProvider(ABC):
    """Abstract interface for User-Agent device metadata parsing."""

    @abstractmethod
    def parse_device_info(self, user_agent: Optional[str]) -> Dict[str, Any]:
        """Parses User-Agent header into structured device metadata dictionary."""
        pass


class DefaultDeviceInfoProvider(DeviceInfoProvider):
    """Zero-dependency robust User-Agent parser extracting browser, OS, and device type."""

    def parse_device_info(self, user_agent: Optional[str]) -> Dict[str, Any]:
        if not user_agent or not isinstance(user_agent, str):
            ua = "Unknown / Direct API"
        else:
            ua = user_agent.strip()

        ua_lower = ua.lower()
        ua_hash = hashlib.sha256(ua.encode("utf-8")).hexdigest()[:16]

        # 1. Device Type & Bot Detection
        is_bot = any(
            b in ua_lower
            for b in [
                "bot",
                "crawler",
                "spider",
                "postman",
                "curl",
                "wget",
                "python-httpx",
                "httpclient",
            ]
        )
        is_mobile = any(
            m in ua_lower
            for m in ["iphone", "android", "mobile", "ipod", "windows phone"]
        )
        is_tablet = any(t in ua_lower for t in ["ipad", "tablet", "kindle"])

        if is_bot:
            device_type = "bot"
        elif is_tablet:
            device_type = "tablet"
        elif is_mobile:
            device_type = "mobile"
        else:
            device_type = "desktop"

        # 2. Operating System & OS Version
        os = "Unknown"
        os_ver = "Unknown"
        if "macintosh" in ua_lower or "mac os x" in ua_lower:
            os = "macOS"
            m = re.search(r"mac os x ([0-9_]+)", ua_lower)
            if m:
                os_ver = m.group(1).replace("_", ".")
        elif "windows" in ua_lower:
            os = "Windows"
            if "nt 10.0" in ua_lower:
                os_ver = "10 / 11"
            elif "nt 6.3" in ua_lower:
                os_ver = "8.1"
            elif "nt 6.1" in ua_lower:
                os_ver = "7"
        elif "android" in ua_lower:
            os = "Android"
            m = re.search(r"android ([0-9.]+)", ua_lower)
            if m:
                os_ver = m.group(1)
        elif "iphone" in ua_lower or "ipad" in ua_lower or "cpu os" in ua_lower:
            os = "iOS"
            m = re.search(r"os ([0-9_]+)", ua_lower)
            if m:
                os_ver = m.group(1).replace("_", ".")
        elif "linux" in ua_lower:
            os = "Linux"

        # 3. Browser & Browser Version
        browser = "Unknown"
        browser_ver = "Unknown"
        if "edg/" in ua_lower:
            browser = "Edge"
            m = re.search(r"edg/([0-9.]+)", ua_lower)
            if m:
                browser_ver = m.group(1)
        elif "chrome/" in ua_lower and "safari/" in ua_lower:
            browser = "Chrome"
            m = re.search(r"chrome/([0-9.]+)", ua_lower)
            if m:
                browser_ver = m.group(1)
        elif "firefox/" in ua_lower:
            browser = "Firefox"
            m = re.search(r"firefox/([0-9.]+)", ua_lower)
            if m:
                browser_ver = m.group(1)
        elif "safari/" in ua_lower and "chrome/" not in ua_lower:
            browser = "Safari"
            m = re.search(r"version/([0-9.]+)", ua_lower)
            if m:
                browser_ver = m.group(1)
        elif "postmanruntime" in ua_lower:
            browser = "Postman Runtime"
        elif "python-httpx" in ua_lower:
            browser = "HTTPX Client"

        return {
            "device_type": device_type,
            "browser": browser,
            "browser_version": browser_ver,
            "operating_system": os,
            "os_version": os_ver,
            "is_mobile": is_mobile,
            "is_bot": is_bot,
            "user_agent_raw": ua,
            "user_agent_hash": ua_hash,
        }
