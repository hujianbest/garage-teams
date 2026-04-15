"""Tests for SessionManager checkpoint recovery mechanism."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from garage_os.runtime.session_manager import SessionManager
from garage_os.storage import FileStorage
from garage_os.types import SessionState


@pytest.fixture
def storage(tmp_path: Path):
    """Create a FileStorage instance for testing."""
    return FileStorage(tmp_path)


@pytest.fixture
def session_manager(storage: FileStorage):
    """Create a SessionManager instance for testing."""
    return SessionManager(storage)


def test_recover_session_level1_valid_session_json(storage, session_manager, tmp_path):
    """session.json 有效时，recover_session 直接从 session.json 恢复。"""
    # 创建 session
    created = session_manager.create_session(
        pack_id="test-pack",
        topic="Test topic",
        user_goals=["goal1"],
        constraints=["constraint1"],
    )

    # 调用 recover_session
    result = session_manager.recover_session(created.session_id)

    # 验证恢复成功
    assert result is not None
    assert result.metadata.session_id == created.session_id
    assert result.metadata.pack_id == created.pack_id
    assert result.metadata.topic == created.topic
    assert result.recovery_method == "session_json"
    assert len(result.recovery_log) > 0


def test_recover_session_level2_corrupt_session_json_use_checkpoint(
    storage, session_manager, tmp_path
):
    """session.json 损坏（checksum 不匹配）时，从最新 checkpoint 恢复。"""
    # 创建 session
    created = session_manager.create_session("test-pack", "Test topic")

    # 创建 checkpoint（含 state_snapshot）
    state_snapshot = {"counter": 42, "status": "ok"}
    checkpoint = session_manager.create_checkpoint(
        created.session_id, "node-abc", state_snapshot
    )

    # 手动篡改 session.json 的 checksum 字段使其不匹配
    session_file = tmp_path / "sessions" / "active" / created.session_id / "session.json"
    data = json.loads(session_file.read_text())
    data["checksum"] = "x" * 64  # 错误的 checksum
    session_file.write_text(json.dumps(data))

    # 调用 recover_session
    result = session_manager.recover_session(created.session_id)

    # 验证恢复成功
    assert result is not None
    assert result.metadata.session_id == created.session_id
    assert result.recovery_method == "checkpoint"
    assert "checkpoint" in result.recovery_log[-1] or "restored" in result.recovery_log[-1]


def test_recover_session_level3_latest_checkpoint_corrupt(
    storage, session_manager, tmp_path
):
    """最新 checkpoint 损坏时，回退到上一个有效 checkpoint。"""
    # 创建 session
    created = session_manager.create_session("test-pack", "Test topic")

    # 创建 checkpoint1（有效）
    state_snapshot1 = {"counter": 10}
    checkpoint1 = session_manager.create_checkpoint(
        created.session_id, "node-1", state_snapshot1
    )

    # 创建 checkpoint2（损坏）
    state_snapshot2 = {"counter": 20}
    checkpoint2 = session_manager.create_checkpoint(
        created.session_id, "node-2", state_snapshot2
    )

    # 篡改 checkpoint2 的 checksum
    checkpoint2_file = (
        tmp_path
        / "sessions"
        / "active"
        / created.session_id
        / "checkpoints"
        / f"{checkpoint2.checkpoint_id}.json"
    )
    cp2_data = json.loads(checkpoint2_file.read_text())
    cp2_data["checksum"] = "y" * 64  # 错误的 checksum
    checkpoint2_file.write_text(json.dumps(cp2_data))

    # 篡改 session.json 的 checksum
    session_file = tmp_path / "sessions" / "active" / created.session_id / "session.json"
    session_data = json.loads(session_file.read_text())
    session_data["checksum"] = "z" * 64
    session_file.write_text(json.dumps(session_data))

    # 调用 recover_session
    result = session_manager.recover_session(created.session_id)

    # 验证从 checkpoint1 恢复
    assert result is not None
    assert result.metadata.session_id == created.session_id
    assert result.recovery_method == "checkpoint_fallback"
    # 应该从 checkpoint1 恢复
    assert "fallback" in result.recovery_log[-1].lower() or "previous" in result.recovery_log[-1].lower()


def test_recover_session_level4_artifact_first_rebuild(
    storage, session_manager, tmp_path
):
    """所有 checkpoint 损坏时，从 artifacts 目录重建。"""
    # 创建 session
    created = session_manager.create_session("test-pack", "Test topic")

    # 在 artifacts 目录下放几个文件
    artifacts_dir = tmp_path / "sessions" / "active" / created.session_id / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "artifact1.txt").write_text("content1")
    (artifacts_dir / "artifact2.md").write_text("content2")

    # 篡改 session.json 的 checksum
    session_file = tmp_path / "sessions" / "active" / created.session_id / "session.json"
    data = json.loads(session_file.read_text())
    data["checksum"] = "x" * 64
    session_file.write_text(json.dumps(data))

    # 调用 recover_session（没有 checkpoint 或所有 checkpoint 都损坏）
    result = session_manager.recover_session(created.session_id)

    # 验证恢复成功
    assert result is not None
    assert result.metadata.session_id == created.session_id
    assert result.recovery_method == "artifact_first"
    # 验证 artifacts 被收集
    assert len(result.metadata.artifacts) >= 2  # 至少有 2 个 artifact


def test_recover_session_level5_no_data(storage, session_manager, tmp_path):
    """无任何可恢复数据时返回 None。"""
    # 不创建任何东西，session_id 不存在
    result = session_manager.recover_session("session-nonexistent-001")

    # 验证返回 None
    assert result is None


def test_recover_session_detects_corrupt_checksum(storage, session_manager, tmp_path):
    """checksum 校验能检测到损坏的数据。"""
    # 创建 session
    created = session_manager.create_session("test-pack", "Test topic")

    # 篡改 session.json 的 state 字段但不更新 checksum
    session_file = tmp_path / "sessions" / "active" / created.session_id / "session.json"
    data = json.loads(session_file.read_text())
    original_checksum = data["checksum"]
    data["state"] = "corrupted_state"
    session_file.write_text(json.dumps(data))

    # 调用 recover_session，验证它检测到损坏并走降级路径
    result = session_manager.recover_session(created.session_id)

    # checksum 校验应该失败，但由于没有 checkpoint，会走到 artifact_first 或返回 None
    # 如果没有 artifact，应该返回 None
    # 如果有 artifact，应该用 artifact_first
    if result is None:
        # 没有 artifact，返回 None
        pass
    else:
        # 有 artifact 或 checkpoint，走降级路径
        assert result.recovery_method in ("checkpoint", "checkpoint_fallback", "artifact_first")
        # 不应该是 session_json，因为 checksum 校验失败
        assert result.recovery_method != "session_json"
