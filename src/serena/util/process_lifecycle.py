"""Process lifecycle management for MCP server.

This module provides comprehensive process management to prevent orphaned processes
and ensure clean shutdown when parent processes (like Claude Code) exit.

Key features:
- PID file management to detect and cleanup old instances
- Signal handlers for graceful shutdown
- Parent process health monitoring (1-second interval)

Note: stdin EOF monitoring was removed as it conflicts with FastMCP's stdio transport.
The parent process health check provides sufficient coverage for detecting parent exit.
"""

import asyncio
import atexit
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class ProcessLifecycleManager:
    """Manages MCP server process lifecycle to prevent orphaned processes."""

    def __init__(self, pid_file_path: Optional[str] = None):
        """Initialize process lifecycle manager.

        Args:
            pid_file_path: Path to PID file. Defaults to /tmp/evolvai-mcp-server.pid

        """
        self.pid_file = Path(pid_file_path or "/tmp/evolvai-mcp-server.pid")
        self.parent_pid = os.getppid()
        self.shutdown_initiated = False
        self._parent_monitor_task: Optional[asyncio.Task] = None

    def setup(self) -> None:
        """Setup all lifecycle management mechanisms.

        This should be called early in the MCP server startup process.
        """
        self._cleanup_old_instance()
        self._create_pid_file()
        self._setup_signal_handlers()
        log.info(
            "Process lifecycle manager initialized (PID: %d, PPID: %d, PID file: %s)",
            os.getpid(),
            self.parent_pid,
            self.pid_file,
        )

    def _cleanup_old_instance(self) -> None:
        """Detect and cleanup old MCP server instances."""
        if not self.pid_file.exists():
            return

        try:
            old_pid = int(self.pid_file.read_text().strip())
        except (ValueError, OSError) as e:
            log.warning("Could not read PID file %s: %s", self.pid_file, e)
            self.pid_file.unlink(missing_ok=True)
            return

        # Check if old process is still running
        try:
            os.kill(old_pid, 0)  # Signal 0 just checks if process exists
            log.warning("Found old MCP server process (PID: %d), terminating it", old_pid)
            try:
                os.kill(old_pid, signal.SIGTERM)
                # Wait up to 3 seconds for graceful shutdown
                for _ in range(6):
                    time.sleep(0.5)
                    try:
                        os.kill(old_pid, 0)
                    except OSError:
                        log.info("Old process %d terminated gracefully", old_pid)
                        break
                else:
                    # Force kill if still running
                    log.warning("Old process %d did not terminate gracefully, force killing", old_pid)
                    os.kill(old_pid, signal.SIGKILL)
            except OSError as e:
                log.warning("Error killing old process %d: %s", old_pid, e)
        except OSError:
            # Process doesn't exist, just clean up the stale PID file
            log.info("Cleaning up stale PID file (process %d doesn't exist)", old_pid)

        self.pid_file.unlink(missing_ok=True)

    def _create_pid_file(self) -> None:
        """Create PID file with current process ID."""
        try:
            self.pid_file.parent.mkdir(parents=True, exist_ok=True)
            self.pid_file.write_text(str(os.getpid()))
            atexit.register(self._cleanup_pid_file)
            log.debug("Created PID file: %s", self.pid_file)
        except OSError as e:
            log.warning("Could not create PID file %s: %s", self.pid_file, e)

    def _cleanup_pid_file(self) -> None:
        """Remove PID file on process exit."""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
                log.debug("Cleaned up PID file: %s", self.pid_file)
        except OSError as e:
            log.warning("Could not remove PID file %s: %s", self.pid_file, e)

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame) -> None:  # type: ignore
            """Handle shutdown signals."""
            if self.shutdown_initiated:
                log.warning("Shutdown already initiated, ignoring signal %d", signum)
                return

            self.shutdown_initiated = True
            signal_name = signal.Signals(signum).name
            log.info("Received %s (signal %d), initiating graceful shutdown", signal_name, signum)

            # Cleanup PID file
            self._cleanup_pid_file()

            # Exit gracefully
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        log.debug("Signal handlers installed (SIGTERM, SIGINT)")

    # stdin EOF monitor removed - conflicts with FastMCP's stdio transport
    # FastMCP needs exclusive access to stdin for reading MCP requests
    # Parent process health monitoring provides sufficient coverage

    async def start_parent_monitor(self, check_interval: float = 1.0) -> None:
        """Start monitoring parent process health.

        Args:
            check_interval: Seconds between health checks

        """
        if self._parent_monitor_task is not None:
            log.warning("Parent monitor already running")
            return

        self._parent_monitor_task = asyncio.create_task(self._parent_monitor_loop(check_interval))
        log.info("Started parent process monitor (PPID: %d, interval: %.1fs)", self.parent_pid, check_interval)

    async def _parent_monitor_loop(self, check_interval: float) -> None:
        """Monitor parent process and exit if it dies."""
        try:
            while True:
                await asyncio.sleep(check_interval)

                try:
                    # Check if parent process still exists
                    os.kill(self.parent_pid, 0)
                except OSError:
                    # Parent process died
                    log.warning("Parent process (PPID: %d) no longer exists, shutting down MCP server", self.parent_pid)
                    self.shutdown_initiated = True
                    self._cleanup_pid_file()
                    os._exit(0)  # Force immediate exit

        except Exception as e:
            log.exception("Error in parent monitor: %s", e)

    def stop(self) -> None:
        """Stop all monitoring tasks and cleanup."""
        self.shutdown_initiated = True

        if self._parent_monitor_task:
            self._parent_monitor_task.cancel()
            self._parent_monitor_task = None

        self._cleanup_pid_file()
        log.info("Process lifecycle manager stopped")
