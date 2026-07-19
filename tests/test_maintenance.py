from __future__ import annotations

import fcntl
import os
import threading
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.maintenance import GateActive, MaintenanceGate, _require_private_tree, resolve_data_root


def private_dir(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path

def test_direct_layout_preserves_existing_root(tmp_path):
    assert resolve_data_root(tmp_path, pointer_layout=False) == (tmp_path, tmp_path)

@pytest.mark.parametrize(("name", "symlink"), [("current", False), ("datasets", True)])
def test_direct_layout_rejects_malformed_adopted_storage_root(tmp_path, name, symlink):
    sentinel = tmp_path / name
    creator = sentinel.symlink_to if symlink else sentinel.write_text
    creator("missing" if symlink else "interrupted")
    with pytest.raises(RuntimeError, match="requires pointer mode"):
        resolve_data_root(tmp_path, pointer_layout=False)

def test_pointer_layout_accepts_only_private_legacy_dataset(tmp_path):
    tmp_path.chmod(0o700)
    datasets = private_dir(tmp_path / "datasets")
    legacy = private_dir(datasets / "legacy")
    (tmp_path / "current").symlink_to(Path("datasets/legacy"))
    assert resolve_data_root(tmp_path, pointer_layout=True) == (legacy, tmp_path)
    (tmp_path / "current").unlink()
    private_dir(datasets / "candidate")
    (tmp_path / "current").symlink_to(Path("datasets/candidate"))
    with pytest.raises(RuntimeError, match="legacy dataset"):
        resolve_data_root(tmp_path, pointer_layout=True)

def test_pointer_layout_rejects_unsafe_dataset_children(tmp_path):
    tmp_path.chmod(0o700)
    datasets = private_dir(tmp_path / "datasets")
    legacy = private_dir(datasets / "legacy")
    unsafe = legacy / "metadata.sqlite3"
    unsafe.write_text("synthetic", encoding="utf-8")
    unsafe.chmod(0o644)
    (tmp_path / "current").symlink_to(Path("datasets/legacy"))
    with pytest.raises(RuntimeError, match="mode 0600"):
        resolve_data_root(tmp_path, pointer_layout=True)

def test_pointer_layout_rejects_non_private_directories(tmp_path):
    tmp_path.chmod(0o755)
    with pytest.raises(RuntimeError, match="mode 0700"):
        resolve_data_root(tmp_path, pointer_layout=True)

@pytest.mark.parametrize(("method", "operation"), [("resolve", lambda root: resolve_data_root(root, pointer_layout=True)), ("lstat", lambda root: MaintenanceGate(root).active), ("walk", _require_private_tree)])
def test_filesystem_errors_do_not_expose_private_paths(tmp_path, monkeypatch, method, operation):
    private = "/private/health/identifying"
    if method == "walk":
        def fail_walk(*args, on_error=None, **kwargs):
            on_error(OSError(private))
            return iter(())
        monkeypatch.setattr(Path, method, fail_walk)
    else:
        monkeypatch.setattr(Path, method, Mock(side_effect=OSError(private)))
    with pytest.raises(RuntimeError) as captured:
        operation(tmp_path)
    assert private not in str(captured.value)

def test_active_gate_rejects_before_opening_lock(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    gate.activate()
    monkeypatch.setattr(gate, "_open_lock", lambda: pytest.fail("lock opened"))
    with pytest.raises(GateActive), gate.admit():
        pass

def test_gate_rechecks_marker_after_shared_lock(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    original = gate._open_lock
    def open_then_gate():
        descriptor = original()
        gate.activate()
        return descriptor
    monkeypatch.setattr(gate, "_open_lock", open_then_gate)
    with pytest.raises(GateActive), gate.admit():
        pass

def test_busy_lock_fails_without_waiting(tmp_path):
    gate = MaintenanceGate(tmp_path)
    descriptor = gate._open_lock()
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    try:
        with pytest.raises(GateActive), gate.admit():
            pass
    finally:
        os.close(descriptor)

def test_drain_waits_for_admitted_writer_and_blocks_new_writers(tmp_path):
    gate = MaintenanceGate(tmp_path)
    admitted = threading.Event()
    release = threading.Event()
    drained = threading.Event()
    def writer() -> None:
        with gate.admit():
            admitted.set()
            release.wait(timeout=2)
    def operator() -> None:
        with gate.drain():
            drained.set()
    writer_thread = threading.Thread(target=writer, daemon=True)
    writer_thread.start()
    assert admitted.wait(timeout=1)
    operator_thread = threading.Thread(target=operator, daemon=True)
    operator_thread.start()
    assert not drained.wait(timeout=0.1)
    with pytest.raises(GateActive), gate.admit():
        pass
    release.set()
    writer_thread.join(timeout=1)
    operator_thread.join(timeout=1)
    assert not writer_thread.is_alive() and not operator_thread.is_alive() and drained.is_set()
def test_marker_is_durable_private_and_restart_visible(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    gate.activate()
    marker = tmp_path / "maintenance" / "ingestion.gate"
    assert marker.stat().st_mode & 0o777 == 0o600 and MaintenanceGate(tmp_path).active
    marker.parent.chmod(0o755)
    for operation in (lambda: gate.active, gate.deactivate):
        with pytest.raises(RuntimeError, match="mode 0700"):
            operation()
        assert marker.exists()
    marker.parent.chmod(0o700)
    gate.deactivate()
    assert not marker.exists()
    marker.parent.rmdir()
    monkeypatch.setattr(os, "fsync", sync := Mock())
    gate.activate()
    assert sync.call_count == 3

@pytest.mark.parametrize("failed_sync", [1, 2, 3])
def test_failed_marker_sync_leaves_activation_retryable(tmp_path, monkeypatch, failed_sync):
    gate = MaintenanceGate(tmp_path)
    effects = [None, None, None, None]
    effects[failed_sync - 1] = OSError("/private/health/identifying")
    monkeypatch.setattr(os, "fsync", Mock(side_effect=effects))
    with pytest.raises(RuntimeError):
        gate.activate()
    gate.activate()
    assert gate.active

def test_failed_marker_removal_sync_is_retryable(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    gate.activate()
    monkeypatch.setattr(os, "fsync", Mock(side_effect=[OSError("private"), None, None, None, None]))
    with pytest.raises(RuntimeError):
        gate.deactivate()
    gate.deactivate()
    assert not gate.active
    gate.activate()
    unlink = gate.marker.unlink
    def raced_unlink(*, missing_ok=False):
        unlink()
        unlink(missing_ok=missing_ok)
    monkeypatch.setattr(Path, "unlink", lambda path, **kwargs: raced_unlink(**kwargs))
    gate.deactivate()

def test_symlinked_lock_is_rejected(tmp_path):
    maintenance = private_dir(tmp_path / "maintenance")
    target = tmp_path / "elsewhere"
    target.write_text("synthetic", encoding="utf-8")
    os.chmod(target, 0o600)
    (maintenance / "ingestion.lock").symlink_to(target)
    with pytest.raises(RuntimeError, match="private regular file"):
        with MaintenanceGate(tmp_path).admit():
            pass
