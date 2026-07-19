from __future__ import annotations

import fcntl
import os
import threading
from pathlib import Path

import pytest

from src.maintenance import GateActive, MaintenanceGate, resolve_data_root


def private_dir(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path

def test_direct_layout_preserves_existing_root(tmp_path):
    data_root, gate_root = resolve_data_root(tmp_path, pointer_layout=False)
    assert data_root == tmp_path
    assert gate_root == tmp_path

@pytest.mark.parametrize(("name", "symlink"), [("current", False), ("datasets", True)])
def test_direct_layout_rejects_malformed_adopted_storage_root(tmp_path, name, symlink):
    sentinel = tmp_path / name
    if symlink:
        sentinel.symlink_to("missing")
    else:
        sentinel.write_text("interrupted", encoding="utf-8")
    with pytest.raises(RuntimeError, match="requires pointer mode"):
        resolve_data_root(tmp_path, pointer_layout=False)

def test_pointer_layout_accepts_only_private_legacy_dataset(tmp_path):
    tmp_path.chmod(0o700)
    datasets = private_dir(tmp_path / "datasets")
    legacy = private_dir(datasets / "legacy")
    (tmp_path / "current").symlink_to(Path("datasets/legacy"))

    assert resolve_data_root(tmp_path, pointer_layout=True) == (legacy, tmp_path)

    (tmp_path / "current").unlink()
    candidate = private_dir(datasets / "candidate")
    (tmp_path / "current").symlink_to(Path("datasets/candidate"))
    with pytest.raises(RuntimeError, match="legacy dataset"):
        resolve_data_root(tmp_path, pointer_layout=True)
    assert candidate.exists()

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

@pytest.mark.parametrize("mode", [0o755, 0o750])
def test_pointer_layout_rejects_non_private_directories(tmp_path, mode):
    tmp_path.chmod(mode)
    with pytest.raises(RuntimeError, match="mode 0700"):
        resolve_data_root(tmp_path, pointer_layout=True)

def test_active_gate_rejects_before_opening_lock(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    gate.activate()
    monkeypatch.setattr(gate, "_open_lock", lambda: pytest.fail("lock opened"))
    with pytest.raises(GateActive):
        with gate.admit():
            pass

def test_gate_rechecks_marker_after_shared_lock(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    original = gate._open_lock

    def open_then_gate():
        descriptor = original()
        gate.activate()
        return descriptor
    monkeypatch.setattr(gate, "_open_lock", open_then_gate)
    with pytest.raises(GateActive):
        with gate.admit():
            pass

def test_busy_lock_fails_without_waiting(tmp_path):
    gate = MaintenanceGate(tmp_path)
    descriptor = gate._open_lock()
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    try:
        with pytest.raises(GateActive):
            with gate.admit():
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
    writer_thread = threading.Thread(target=writer)
    writer_thread.start()
    assert admitted.wait(timeout=1)
    operator_thread = threading.Thread(target=operator)
    operator_thread.start()
    assert not drained.wait(timeout=0.1)
    with pytest.raises(GateActive):
        with gate.admit():
            pass
    release.set()
    writer_thread.join(timeout=1)
    operator_thread.join(timeout=1)
    assert drained.is_set()

def test_marker_is_durable_private_and_restart_visible(tmp_path):
    gate = MaintenanceGate(tmp_path)
    gate.activate()
    marker = tmp_path / "maintenance" / "ingestion.gate"
    assert marker.stat().st_mode & 0o777 == 0o600
    assert MaintenanceGate(tmp_path).active
    gate.deactivate()
    assert not marker.exists()

@pytest.mark.parametrize("failed_sync", [1, 2])
def test_failed_marker_sync_leaves_activation_retryable(tmp_path, monkeypatch, failed_sync):
    gate = MaintenanceGate(tmp_path)
    original_fsync = os.fsync
    calls = 0
    def fail_once(descriptor):
        nonlocal calls
        calls += 1
        if calls == failed_sync:
            raise OSError
        original_fsync(descriptor)
    monkeypatch.setattr(os, "fsync", fail_once)
    with pytest.raises(OSError):
        gate.activate()
    gate.activate()
    assert gate.active

def test_failed_marker_removal_sync_is_retryable(tmp_path, monkeypatch):
    gate = MaintenanceGate(tmp_path)
    gate.activate()
    original_fsync = os.fsync
    failed = False
    def fail_once(descriptor):
        nonlocal failed
        if not failed:
            failed = True
            raise OSError
        original_fsync(descriptor)
    monkeypatch.setattr(os, "fsync", fail_once)
    with pytest.raises(OSError):
        gate.deactivate()
    gate.deactivate()
    assert not gate.active

def test_symlinked_lock_is_rejected(tmp_path):
    maintenance = private_dir(tmp_path / "maintenance")
    target = tmp_path / "elsewhere"
    target.write_text("synthetic", encoding="utf-8")
    os.chmod(target, 0o600)
    (maintenance / "ingestion.lock").symlink_to(target)
    with pytest.raises(RuntimeError, match="private regular file"):
        with MaintenanceGate(tmp_path).admit():
            pass
