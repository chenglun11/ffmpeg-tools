"""Check for application updates via GitHub Releases API."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import httpx

from ffmpeg_tui import __version__

_GITHUB_API_URL = "https://api.github.com/repos/chenglun11/ffmpeg-tools/releases/latest"
_USER_AGENT = "ffmpeg-tools-updater"


@dataclass
class UpdateInfo:
    latest_version: str
    current_version: str
    download_url: str
    release_notes: str
    published_at: str


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a semver-like string into a tuple of ints for comparison."""
    m = re.match(r"v?(\d+(?:\.\d+)*)", v)
    if not m:
        return (0,)
    return tuple(int(x) for x in m.group(1).split("."))


class UpdateChecker:
    def check_update(self) -> UpdateInfo:
        """Check GitHub for a newer release. Always returns UpdateInfo.

        If no newer version, latest_version == current_version.
        Raises on network/parse errors.
        """
        resp = httpx.get(
            _GITHUB_API_URL,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        data = resp.json()

        tag = data.get("tag_name", "")
        if not tag:
            return UpdateInfo(
                latest_version=__version__,
                current_version=__version__,
                download_url="",
                release_notes="",
                published_at="",
            )

        latest = _parse_version(tag)
        current = _parse_version(__version__)

        return UpdateInfo(
            latest_version=tag.lstrip("v"),
            current_version=__version__,
            download_url=data.get("html_url", ""),
            release_notes=data.get("body", "") or "",
            published_at=data.get("published_at", ""),
        )
