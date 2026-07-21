from __future__ import annotations

import fcntl
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class GateActive(RuntimeError):
    """Raised when ingestion is closed or its admission lock is busy."""


@contextmanager
def _path_neutral(message: str) -> Iterator[None]:
    try:
        yield
    except OSError:
        raise RuntimeError(message) from None


def _validate_private_directory(metadata: os.stat_result) -> None:
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise RuntimeError("Private directory must be owned with mode 0700")


def _open_private_directory(path: Path) -> tuple[int, os.stat_result]:
    with _path_neutral("Private directory is unavailable"):
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            _validate_private_directory(metadata)
            return descriptor, metadata
        except Exception:
            os.close(descriptor)
            raise


def _require_private_directory(path: Path) -> os.stat_result:
    descriptor, metadata = _open_private_directory(path)
    os.close(descriptor)
    return metadata


def _require_private_tree(root: Path) -> None:
    with _path_neutral("Private dataset could not be verified"):
        for directory, directories, files in root.walk(on_error=lambda error: (_ for _ in ()).throw(error)):
            for name in directories:
                _require_private_directory(directory / name)
            for name in files:
                path = directory / name
                metadata = path.lstat()
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
                    raise RuntimeError("Private dataset files must be owned with mode 0600")


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

    with _path_neutral("Installation root could not be resolved"):
        installation_root = configured_root.resolve(strict=True)
    _require_private_directory(installation_root)
    datasets = installation_root / "datasets"
    legacy = datasets / "legacy"
    _require_private_directory(datasets)
    _require_private_directory(legacy)
    current = installation_root / "current"
    with _path_neutral("Current pointer must select the legacy dataset"):
        if not current.is_symlink() or current.resolve(strict=True) != legacy:
            raise RuntimeError("Current pointer must select the legacy dataset")
    _require_private_tree(legacy)
    return legacy, installation_root


class MaintenanceGate:
    def __init__(self, root: Path):
        self.directory = root / "maintenance"
        self.marker = self.directory / "ingestion.gate"
        self.lock_path = self.directory / "ingestion.lock"
        self._directory_identity: tuple[int, int] | None = None

    @property
    def active(self) -> bool:
        if not _lexists(self.directory):
            return False
        descriptor, _ = _open_private_directory(self.directory)
        try:
            return self._marker_active(descriptor)
        finally:
            os.close(descriptor)

    def _marker_active(self, directory: int) -> bool:
        try:
            metadata = os.stat(self.marker.name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            return False
        except OSError:
            raise RuntimeError("Maintenance gate state could not be read") from None
        self._require_private_file(metadata)
        return True

    def _ensure_directory(self) -> None:
        missing = not _lexists(self.directory)
        if missing:
            with _path_neutral("Maintenance directory could not be prepared"):
                try:
                    os.mkdir(self.directory, 0o700)
                except FileExistsError:
                    pass
        metadata = _require_private_directory(self.directory)
        identity = (metadata.st_dev, metadata.st_ino)
        if missing or identity != self._directory_identity:
            self._sync_directory(self.directory.parent)
            self._directory_identity = identity

    def _open_maintenance_directory(self) -> int:
        self._ensure_directory()
        descriptor, _ = _open_private_directory(self.directory)
        return descriptor

    @staticmethod
    def _require_private_file(metadata: os.stat_result) -> None:
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
            raise RuntimeError("Maintenance path must be a private regular file")

    def _open_lock_in(self, directory: int) -> int:
        with _path_neutral("Maintenance path must be a private regular file"):
            descriptor = os.open(self.lock_path.name, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                os.fchmod(descriptor, 0o600)
                self._require_private_file(os.fstat(descriptor))
                return descriptor
            except Exception:
                os.close(descriptor)
                raise

    def _open_lock(self) -> tuple[int, int]:
        directory = self._open_maintenance_directory()
        try:
            return self._open_lock_in(directory), directory
        except Exception:
            os.close(directory)
            raise

    def _sync_directory(self, directory: Path | None = None) -> None:
        directory = directory or self.directory
        with _path_neutral("Maintenance directory could not be synchronized"):
            descriptor = os.open(directory, os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    @staticmethod
    def _sync_open_directory(directory: int) -> None:
        with _path_neutral("Maintenance directory could not be synchronized"):
            os.fsync(directory)

    def activate(self) -> None:
        directory = self._open_maintenance_directory()
        try:
            self._activate(directory)
        finally:
            os.close(directory)

    def _activate(self, directory: int) -> None:
        if self._marker_active(directory):
            self._sync_open_directory(directory)
            return
        temporary = self.directory / f".ingestion.gate.{os.getpid()}.{id(self)}"
        with _path_neutral("Maintenance gate could not be activated"):
            try:
                descriptor = os.open(temporary.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=directory)
                try:
                    os.fchmod(descriptor, 0o600)
                    os.write(descriptor, b"active\n")
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                os.replace(temporary.name, self.marker.name, src_dir_fd=directory, dst_dir_fd=directory)
                self._sync_open_directory(directory)
            finally:
                try:
                    os.unlink(temporary.name, dir_fd=directory)
                except FileNotFoundError:
                    pass

    def deactivate(self) -> None:
        directory = self._open_maintenance_directory()
        try:
            active = self._marker_active(directory)
            if active:
                with _path_neutral("Maintenance gate could not be deactivated"):
                    try:
                        os.unlink(self.marker.name, dir_fd=directory)
                    except FileNotFoundError:
                        pass
            self._sync_open_directory(directory)
        finally:
            os.close(directory)

    @contextmanager
    def admit(self) -> Iterator[None]:
        if self.active:
            raise GateActive("Ingestion maintenance is active")
        descriptor, directory = self._open_lock()
        try:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise GateActive("Ingestion maintenance is active") from error
            if self._marker_active(directory):
                raise GateActive("Ingestion maintenance is active")
            yield
        finally:
            os.close(descriptor)
            os.close(directory)

    @contextmanager
    def drain(self) -> Iterator[None]:
        directory = self._open_maintenance_directory()
        try:
            self._activate(directory)
            descriptor = self._open_lock_in(directory)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                yield
            finally:
                os.close(descriptor)
        finally:
            os.close(directory)
