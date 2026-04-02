"""Check for application updates via GitHub Releases API."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx

from ffmpeg_tui import __version__

_GITHUB_API_URL = "https://api.github.com/repos/chenglun11/ffmpeg-tools/releases/latest"
_USER_AGENT = "ffmpeg-tools-updater"
_MAX_RETRIES = 3
_RETRY_DELAY = 2  # seconds


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
        Raises on network/parse errors with descriptive messages.
        """
        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = httpx.get(
                    _GITHUB_API_URL,
                    timeout=15,
                    follow_redirects=True,
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except httpx.HTTPStatusError as e:
                last_err = e
                if e.response.status_code == 403:
                    # Rate limit — retry after delay
                    if attempt < _MAX_RETRIES - 1:
                        time.sleep(_RETRY_DELAY * (attempt + 1))
                        continue
                    raise UpdateCheckError(
                        "GitHub API 速率限制，请稍后再试"
                    ) from e
                elif e.response.status_code == 404:
                    raise UpdateCheckError(
                        "未找到发布信息，仓库可能尚无 Release"
                    ) from e
                else:
                    raise UpdateCheckError(
                        f"服务器返回错误 ({e.response.status_code})"
                    ) from e
            except httpx.TimeoutException as e:
                last_err = e
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAY)
                    continue
                raise UpdateCheckError("连接超时，请检查网络") from e
            except httpx.ConnectError as e:
                last_err = e
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAY)
                    continue
                raise UpdateCheckError("无法连接到 GitHub，请检查网络") from e
            except Exception as e:
                raise UpdateCheckError(f"检查更新失败: {e}") from e
        else:
            raise UpdateCheckError(f"重试 {_MAX_RETRIES} 次后仍然失败") from last_err

        tag = data.get("tag_name", "")
        if not tag:
            return UpdateInfo(
                latest_version=__version__,
                current_version=__version__,
                download_url="",
                release_notes="",
                published_at="",
            )

        return UpdateInfo(
            latest_version=tag.lstrip("v"),
            current_version=__version__,
            download_url=data.get("html_url", ""),
            release_notes=data.get("body", "") or "",
            published_at=data.get("published_at", ""),
        )


class UpdateCheckError(Exception):
    """Raised when an update check fails with a user-friendly message."""
