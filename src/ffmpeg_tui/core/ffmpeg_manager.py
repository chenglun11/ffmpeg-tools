"""FFmpeg installation detection, download, and management."""

import asyncio
import platform
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

import httpx

from ffmpeg_tui.config import FFMPEG_DIR

# Subdirectory for extracted binaries
_BIN_DIR = FFMPEG_DIR / "bin"

# Suffix for executables on the current platform
_EXE_SUFFIX = ".exe" if platform.system() == "Windows" else ""


class FFmpegManager:
    """Manage FFmpeg detection, download, and installation."""

    def __init__(self) -> None:
        self._ffmpeg_path: Optional[Path] = None
        self._ffprobe_path: Optional[Path] = None

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def check_installation(self) -> bool:
        """Return True if a usable FFmpeg is found (local dir or system PATH)."""
        # 1. Check local installation directory first
        local_ffmpeg = _BIN_DIR / f"ffmpeg{_EXE_SUFFIX}"
        local_ffprobe = _BIN_DIR / f"ffprobe{_EXE_SUFFIX}"

        if local_ffmpeg.is_file() and self.verify_installation(local_ffmpeg):
            self._ffmpeg_path = local_ffmpeg
            self._ffprobe_path = local_ffprobe if local_ffprobe.is_file() else None
            return True

        # 2. Check system PATH
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg is not None:
            ffmpeg_path = Path(sys_ffmpeg)
            if self.verify_installation(ffmpeg_path):
                self._ffmpeg_path = ffmpeg_path
                sys_ffprobe = shutil.which("ffprobe")
                self._ffprobe_path = Path(sys_ffprobe) if sys_ffprobe else None
                return True

        return False

    def get_ffmpeg_path(self) -> Optional[Path]:
        """Return the path to the ffmpeg executable, or None if not found."""
        if self._ffmpeg_path is None:
            self.check_installation()
        return self._ffmpeg_path

    def get_ffprobe_path(self) -> Optional[Path]:
        """Return the path to the ffprobe executable, or None if not found."""
        if self._ffprobe_path is None:
            self.check_installation()
        return self._ffprobe_path

    def get_version(self) -> Optional[str]:
        """Return the FFmpeg version string, or None if unavailable."""
        ffmpeg = self.get_ffmpeg_path()
        if ffmpeg is None:
            return None
        try:
            result = subprocess.run(
                [str(ffmpeg), "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return None
            # First line looks like: "ffmpeg version N-... Copyright ..."
            first_line = result.stdout.split("\n", 1)[0]
            return first_line
        except (subprocess.SubprocessError, OSError):
            return None

    def get_supported_formats(self) -> dict[str, str]:
        """Return a dict mapping format name to description for supported formats.

        Runs ``ffmpeg -formats`` and parses the output.  Returns an empty dict
        if FFmpeg is not available.
        """
        ffmpeg = self.get_ffmpeg_path()
        if ffmpeg is None:
            return {}
        try:
            result = subprocess.run(
                [str(ffmpeg), "-formats"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return {}
        except (subprocess.SubprocessError, OSError):
            return {}

        formats: dict[str, str] = {}
        # Lines look like: " DE avi             AVI (Audio Video Interleaved)"
        parsing = False
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                parsing = True
                continue
            if not parsing or not stripped:
                continue
            parts = stripped.split(None, 2)
            if len(parts) >= 3 and any(c in parts[0] for c in "DE"):
                formats[parts[1]] = parts[2]
        return formats

    def get_supported_codecs(self) -> dict[str, str]:
        """Return a dict mapping codec name to description for supported codecs.

        Runs ``ffmpeg -codecs`` and parses the output.  Returns an empty dict
        if FFmpeg is not available.
        """
        ffmpeg = self.get_ffmpeg_path()
        if ffmpeg is None:
            return {}
        try:
            result = subprocess.run(
                [str(ffmpeg), "-codecs"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return {}
        except (subprocess.SubprocessError, OSError):
            return {}

        codecs: dict[str, str] = {}
        # Lines look like: " DEV.LS h264       H.264 / AVC / MPEG-4 AVC ..."
        parsing = False
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                parsing = True
                continue
            if not parsing or not stripped:
                continue
            parts = stripped.split(None, 2)
            if len(parts) >= 3 and len(parts[0]) >= 6:
                codecs[parts[1]] = parts[2]
        return codecs

    # ------------------------------------------------------------------
    # Download & install
    # ------------------------------------------------------------------

    async def download_ffmpeg(
        self,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    ) -> Path:
        """Download a static FFmpeg build for the current platform.

        Args:
            progress_callback: Called with (downloaded_bytes, total_bytes).
                ``total_bytes`` may be ``None`` when the server does not
                provide a Content-Length header.

        Returns:
            Path to the installed ffmpeg binary.

        Raises:
            RuntimeError: On network, extraction, or permission errors.
        """
        url = self._get_download_url()
        FFMPEG_DIR.mkdir(parents=True, exist_ok=True)

        # Determine archive filename from URL
        archive_name = url.rsplit("/", 1)[-1]
        archive_path = FFMPEG_DIR / archive_name

        # Download
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    total = (
                        int(response.headers["content-length"])
                        if "content-length" in response.headers
                        else None
                    )
                    downloaded = 0
                    with open(archive_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback is not None:
                                progress_callback(downloaded, total)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Failed to download FFmpeg: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Network error while downloading FFmpeg: {exc}") from exc

        # Extract
        try:
            ffmpeg_bin = self._extract_archive(archive_path, FFMPEG_DIR)
        except Exception as exc:
            raise RuntimeError(f"Failed to extract FFmpeg archive: {exc}") from exc
        finally:
            # Clean up the archive regardless of success
            archive_path.unlink(missing_ok=True)

        # Refresh cached paths
        self._ffmpeg_path = ffmpeg_bin
        ffprobe_bin = ffmpeg_bin.parent / f"ffprobe{_EXE_SUFFIX}"
        self._ffprobe_path = ffprobe_bin if ffprobe_bin.is_file() else None

        return ffmpeg_bin

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_download_url() -> str:
        """Return a download URL appropriate for the current platform."""
        system = platform.system().lower()
        machine = platform.machine().lower()

        if system == "windows":
            return (
                "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
                "ffmpeg-master-latest-win64-gpl.zip"
            )
        elif system == "darwin":
            if machine == "arm64":
                return "https://www.osxexperts.net/ffmpeg7arm.zip"
            else:
                return "https://www.osxexperts.net/ffmpeg7intel.zip"
        else:  # linux
            if machine == "aarch64":
                return (
                    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
                    "ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
                )
            else:
                return (
                    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
                    "ffmpeg-master-latest-linux64-gpl.tar.xz"
                )

    def _extract_archive(self, archive_path: Path, target_dir: Path) -> Path:
        """Extract an archive and copy ffmpeg/ffprobe binaries into *_BIN_DIR*.

        Returns:
            Path to the extracted ``ffmpeg`` executable.
        """
        _BIN_DIR.mkdir(parents=True, exist_ok=True)
        extract_dir = target_dir / "_extract_tmp"

        try:
            # Extract
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)
            elif archive_path.name.endswith(".tar.xz"):
                with tarfile.open(archive_path, "r:xz") as tf:
                    tf.extractall(extract_dir)
            else:
                raise RuntimeError(f"Unsupported archive format: {archive_path.name}")

            # Locate ffmpeg binary inside the extracted tree
            ffmpeg_name = f"ffmpeg{_EXE_SUFFIX}"
            ffprobe_name = f"ffprobe{_EXE_SUFFIX}"

            found_ffmpeg: Optional[Path] = None
            found_ffprobe: Optional[Path] = None

            for p in extract_dir.rglob(ffmpeg_name):
                if p.is_file():
                    found_ffmpeg = p
                    break

            for p in extract_dir.rglob(ffprobe_name):
                if p.is_file():
                    found_ffprobe = p
                    break

            if found_ffmpeg is None:
                raise RuntimeError(
                    f"Could not find '{ffmpeg_name}' in the downloaded archive."
                )

            # Copy binaries to _BIN_DIR
            dest_ffmpeg = _BIN_DIR / ffmpeg_name
            shutil.copy2(found_ffmpeg, dest_ffmpeg)

            if found_ffprobe is not None:
                dest_ffprobe = _BIN_DIR / ffprobe_name
                shutil.copy2(found_ffprobe, dest_ffprobe)

            # Set executable permissions on non-Windows platforms
            if platform.system() != "Windows":
                dest_ffmpeg.chmod(0o755)
                if found_ffprobe is not None:
                    (_BIN_DIR / ffprobe_name).chmod(0o755)

            return dest_ffmpeg

        finally:
            # Clean up temporary extraction directory
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)

    @staticmethod
    def verify_installation(path: Path) -> bool:
        """Return True if *path* points to a working ffmpeg binary."""
        try:
            result = subprocess.run(
                [str(path), "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False
