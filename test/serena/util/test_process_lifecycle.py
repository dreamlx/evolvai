"""Tests for ProcessLifecycleManager.

TDD approach - tests written BEFORE fixing the implementation.
"""

import asyncio
import os
import signal
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from serena.util.process_lifecycle import ProcessLifecycleManager

# Use pytest-anyio for async tests
pytestmark = pytest.mark.anyio


class TestProcessLifecycleManager:
    """Test ProcessLifecycleManager behavior."""

    def test_pid_file_creation(self):
        """PID file should be created on setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"
            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))

            # Before setup - no PID file
            assert not pid_file.exists()

            # After setup - PID file exists with current PID
            manager.setup()
            assert pid_file.exists()
            assert int(pid_file.read_text().strip()) == os.getpid()

            # Cleanup
            manager._cleanup_pid_file()
            assert not pid_file.exists()

    def test_cleanup_old_instance(self):
        """Old instances should be terminated on startup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"

            # Create fake old PID file with non-existent PID
            fake_pid = 999999
            pid_file.write_text(str(fake_pid))

            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))
            manager.setup()  # Should not raise, just cleanup

            # PID file should now have current PID
            assert int(pid_file.read_text().strip()) == os.getpid()

            manager._cleanup_pid_file()

    def test_signal_handlers_registered(self):
        """Signal handlers should be registered on setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"
            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))

            # Get original handlers
            original_sigterm = signal.getsignal(signal.SIGTERM)
            original_sigint = signal.getsignal(signal.SIGINT)

            try:
                manager.setup()

                # Handlers should be changed
                new_sigterm = signal.getsignal(signal.SIGTERM)
                new_sigint = signal.getsignal(signal.SIGINT)

                assert new_sigterm != original_sigterm
                assert new_sigint != original_sigint

            finally:
                # Restore original handlers
                signal.signal(signal.SIGTERM, original_sigterm)
                signal.signal(signal.SIGINT, original_sigint)
                manager._cleanup_pid_file()

    async def test_parent_monitor_check_interval(self):
        """Parent monitor should use the specified check interval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"
            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))
            manager.setup()

            # Use real parent (should be alive)
            manager.parent_pid = os.getppid()

            # Start monitor with custom interval
            await manager.start_parent_monitor(check_interval=0.5)

            # Verify task was created
            assert manager._parent_monitor_task is not None
            assert not manager._parent_monitor_task.done()

            # Cleanup
            manager.stop()
            assert manager._parent_monitor_task is None

    async def test_parent_monitor_runs_while_parent_alive(self):
        """Parent monitor should keep running while parent is alive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"
            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))
            manager.setup()

            # Use real parent PID (should be alive)
            manager.parent_pid = os.getppid()

            # Start monitor
            await manager.start_parent_monitor(check_interval=0.1)

            # Wait and verify task is still running
            await asyncio.sleep(0.3)
            assert manager._parent_monitor_task is not None
            assert not manager._parent_monitor_task.done()

            # Cleanup
            manager.stop()
            manager._cleanup_pid_file()

    async def test_no_stdin_monitor_should_exist(self):
        """stdin monitor should NOT exist (conflicts with FastMCP)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"
            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))
            manager.setup()

            # Verify no stdin monitor method exists or is disabled
            # This is the key test - we should NOT have stdin monitoring
            assert not hasattr(manager, "start_stdin_monitor") or manager.start_stdin_monitor is None

            manager._cleanup_pid_file()

    def test_default_pid_file_location(self):
        """Default PID file should be in /tmp."""
        manager = ProcessLifecycleManager()
        assert manager.pid_file == Path("/tmp/evolvai-mcp-server.pid")


class TestProcessLifecycleIntegration:
    """Integration tests for complete lifecycle scenarios."""

    async def test_full_lifecycle(self):
        """Test complete lifecycle: setup -> monitor -> cleanup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"
            manager = ProcessLifecycleManager(pid_file_path=str(pid_file))

            # 1. Setup
            manager.setup()
            assert pid_file.exists()
            assert int(pid_file.read_text().strip()) == os.getpid()

            # 2. Start monitoring
            manager.parent_pid = os.getppid()  # Real parent
            await manager.start_parent_monitor(check_interval=0.1)
            await asyncio.sleep(0.2)

            # 3. Stop
            manager.stop()
            assert manager.shutdown_initiated

            # 4. Cleanup
            manager._cleanup_pid_file()
            assert not pid_file.exists()

    async def test_multiple_startups_cleanup_old_instance(self):
        """Multiple startups should cleanup old instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_file = Path(tmpdir) / "test.pid"

            # First instance
            manager1 = ProcessLifecycleManager(pid_file_path=str(pid_file))
            manager1.setup()
            pid1 = int(pid_file.read_text().strip())
            assert pid1 == os.getpid()

            # Second instance (simulate restart)
            # Write fake old PID
            pid_file.write_text("999999")

            manager2 = ProcessLifecycleManager(pid_file_path=str(pid_file))
            manager2.setup()
            pid2 = int(pid_file.read_text().strip())

            # Should have current PID now
            assert pid2 == os.getpid()
            assert pid2 == pid1  # Same process

            manager2._cleanup_pid_file()
