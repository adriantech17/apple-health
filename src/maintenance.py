from __future__ import annotations

import fcntl
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class GateActive(RuntimeError):
    """Raised when ingestion is closed or its admission lock is busy."""


def _require_private_directory(path: Path) -> None:
    try:
        metadata = path.lstat()
    except OSError:
        raise RuntimeError("Private directory is unavailable") from None
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise RuntimeError("Private directory must be owned with mode 0700")


def _require_private_tree(root: Path) -> None:
    try:
        for path in root.rglob("*"):
            metadata = path.lstat()
            if stat.S_ISDIR(metadata.st_mode):
                _require_private_directory(path)
            elif not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
                raise RuntimeError("Private dataset files must be owned with mode 0600")
    except OSError:
        raise RuntimeError("Private dataset could not be verified") from None


def _lexists(path: Path) -> bool:
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False
    except OSError:
        raise RuntimeError("Storage layout could not be verified") from None


def resolve_data_root(configured_root: Path, *, pointer_layout: bool) -> tuple[Path, Path]:
    if not pointer_layout:
        if _lexists(configured_root / "current") or _lexists(configured_root / "datasets"):
            raise RuntimeError("Adopted storage layout requires pointer mode")
        return configured_root, configured_root

    installation_root = configured_root.resolve(strict=True)
    _require_private_directory(installation_root)
    datasets = installation_root / "datasets"
    legacy = datasets / "legacy"
    _require_private_directory(datasets)
    _require_private_directory(legacy)
    current = installation_root / "current"
    try:
        if not current.is_symlink() or current.resolve(strict=True) != legacy:
            raise RuntimeError("Current pointer must select the legacy dataset")
    except OSError:
        raise RuntimeError("Current pointer must select the legacy dataset") from None
    _require_private_tree(legacy)
    return legacy, installation_root


class MaintenanceGate:
    def __init__(self, root: Path):
        self.directory = root / "maintenance"
        self.marker = self.directory / "ingestion.gate"
        self.lock_path = self.directory / "ingestion.lock"

    @property
    def active(self) -> bool:
        try:
            metadata = self.marker.lstat()
        except FileNotFoundError:
            return False
        self._require_private_file(metadata)
        return True

    def _ensure_directory(self) -> None:
        try:
            self.directory.mkdir(mode=0o700)
        except FileExistsError:
            pass
        _require_private_directory(self.directory)

    @staticmethod
    def _require_private_file(metadata: os.stat_result) -> None:
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise RuntimeError("Maintenance path must be a private regular file")

    def _open_lock(self) -> int:
        self._ensure_directory()
        flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
        try:
            descriptor = os.open(self.lock_path, flags, 0o600)
        except OSError:
            raise RuntimeError("Maintenance path must be a private regular file") from None
        try:
            os.fchmod(descriptor, 0o600)
            self._require_private_file(os.fstat(descriptor))
            return descriptor
        except Exception:
            os.close(descriptor)
            raise

    def _sync_directory(self) -> None:
        descriptor = os.open(self.directory, os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def activate(self) -> None:
        self._ensure_directory()
        if self.active:
            self._sync_directory()
            return
        temporary = self.directory / f".ingestion.gate.{os.getpid()}.{id(self)}"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
        try:
            descriptor = os.open(temporary, flags, 0o600)
            try:
                os.fchmod(descriptor, 0o600)
                os.write(descriptor, b"active\n")
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.replace(temporary, self.marker)
            self._sync_directory()
        finally:
            temporary.unlink(missing_ok=True)

    def deactivate(self) -> None:
        if not self.active:
            self._ensure_directory()
            self._sync_directory()
            return
        self.marker.unlink()
        self._sync_directory()

    @contextmanager
    def admit(self) -> Iterator[None]:
        if self.active:
            raise GateActive("Ingestion maintenance is active")
        descriptor = self._open_lock()
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise GateActive("Ingestion maintenance is active") from error
            if self.active:
                raise GateActive("Ingestion maintenance is active")
            yield
        finally:
            os.close(descriptor)

    @contextmanager
    def drain(self) -> Iterator[None]:
        self.activate()
        descriptor = self._open_lock()
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            yield
        finally:
            os.close(descriptor)
