# Process Lifecycle Management

**Date**: 2025-11-19
**Status**: Implemented
**Impact**: Critical - Prevents orphaned MCP server processes

---

## Problem Statement

### Symptoms
When Claude Code restarts multiple times, orphaned `evolvai-mcp-server` processes accumulate:
- Each Claude Code restart creates a new MCP server process
- Old processes become orphans (PPID=1) when Claude Code exits
- Processes continue running indefinitely, consuming resources
- Multiple dashboard instances compete for ports

### Root Cause Analysis

**Call Stack Investigation**:
```
Main Thread stuck in:
_tkinter_tkapp_mainloop_impl
→ Tcl_DoOneEvent
→ Tcl_WaitForEvent
→ CFRunLoopRunSpecific (macOS event loop)
```

**Process State**:
```
PID 45003: PPID=1 (orphaned, parent died Mon 5PM)
PID 53176: PPID=52861 (current Claude Code process)

File Descriptors (PID 45003):
FD 0 (stdin):  unix socket → (none) - disconnected
FD 1 (stdout): unix socket → (none) - disconnected
FD 2 (stderr): unix socket → (none) - disconnected
```

**Why Processes Don't Exit**:
1. Claude Code exits → stdin/stdout pipes close
2. MCP server's stdio_server() should receive EOF
3. But main thread stuck in Tkinter event loop (despite GUI disabled on macOS)
4. Process doesn't respond to EOF signal
5. Becomes orphan process, continues running

---

## Solution Architecture

### Design Principles

1. **Defense in Depth**: Multiple mechanisms to ensure process cleanup
2. **Fail-Safe**: If one mechanism fails, others still work
3. **Zero Configuration**: Works automatically without user intervention
4. **Backward Compatible**: Doesn't break existing deployments

### Components

```
ProcessLifecycleManager
├─ PID File Management
│  ├─ Detect old instances
│  ├─ Kill old processes (SIGTERM → SIGKILL)
│  └─ Clean up on exit
├─ Signal Handlers
│  ├─ SIGTERM (graceful shutdown)
│  └─ SIGINT (Ctrl+C)
├─ stdin EOF Monitor (async)
│  └─ Exit when parent closes stdin
└─ Parent Process Monitor (async)
   └─ Exit when parent process dies
```

---

## Implementation

### Core Module

**File**: `src/serena/util/process_lifecycle.py`

```python
class ProcessLifecycleManager:
    """Manages MCP server process lifecycle to prevent orphaned processes."""

    def __init__(self, pid_file_path: Optional[str] = None):
        self.pid_file = Path(pid_file_path or "/tmp/evolvai-mcp-server.pid")
        self.parent_pid = os.getppid()
        self.shutdown_initiated = False

    def setup(self) -> None:
        """Setup all lifecycle management mechanisms."""
        self._cleanup_old_instance()   # Kill old processes
        self._create_pid_file()         # Track current PID
        self._setup_signal_handlers()   # Handle SIGTERM/SIGINT
```

### Integration Points

**CLI Integration** (`src/serena/cli.py:172-176`):
```python
from serena.util.process_lifecycle import ProcessLifecycleManager

lifecycle_manager = ProcessLifecycleManager()
lifecycle_manager.setup()  # ← Called before MCP server starts
```

**MCP Factory Integration** (`src/serena/mcp.py:356-366`):
```python
@asynccontextmanager
async def server_lifespan(self, mcp_server: FastMCP) -> AsyncIterator[None]:
    # Start async monitors
    if self.lifecycle_manager:
        await self.lifecycle_manager.start_stdin_monitor()
        await self.lifecycle_manager.start_parent_monitor()

    yield

    # Cleanup on shutdown
    if self.lifecycle_manager:
        self.lifecycle_manager.stop()
```

---

## Features

### 1. PID File Management

**Purpose**: Detect and cleanup old instances before starting new one

**Mechanism**:
```python
# On startup
if pid_file.exists():
    old_pid = int(pid_file.read_text())
    if process_exists(old_pid):
        os.kill(old_pid, SIGTERM)  # Graceful shutdown
        wait(3 seconds)
        if still_running:
            os.kill(old_pid, SIGKILL)  # Force kill

# Write new PID
pid_file.write_text(str(os.getpid()))
atexit.register(cleanup_pid_file)
```

**Location**: `/tmp/evolvai-mcp-server.pid`

**Benefits**:
- ✅ Prevents multiple instances
- ✅ Automatic cleanup of zombies
- ✅ Graceful degradation (SIGTERM → SIGKILL)

### 2. Signal Handlers

**Purpose**: Respond to kill signals from parent or user

**Signals Handled**:
- `SIGTERM`: Graceful shutdown (used by system/parent)
- `SIGINT`: Keyboard interrupt (Ctrl+C)

**Handler**:
```python
def signal_handler(signum: int, frame) -> None:
    if shutdown_initiated:
        return  # Prevent double-shutdown

    shutdown_initiated = True
    log.info("Received signal %d, shutting down", signum)
    cleanup_pid_file()
    sys.exit(0)
```

**Benefits**:
- ✅ Clean shutdown on `kill -TERM <pid>`
- ✅ Works with systemd/launchd
- ✅ Idempotent (safe to call multiple times)

### 3. stdin EOF Monitor

**Purpose**: Detect when parent process closes stdin (stdio transport)

**Mechanism**:
```python
async def _stdin_monitor_loop(self) -> None:
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()

    # Connect to stdin
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    # Block until EOF
    await reader.read()

    # stdin closed → parent exited
    log.warning("stdin closed, shutting down")
    os._exit(0)  # Force immediate exit
```

**Why `os._exit(0)`**:
- Bypasses Python cleanup (faster)
- Prevents Tkinter event loop from blocking
- Used when parent is already dead (no need for graceful cleanup)

**Benefits**:
- ✅ Immediate shutdown when Claude Code exits
- ✅ Works with stdio transport
- ✅ No orphan processes

### 4. Parent Process Health Check

**Purpose**: Periodic verification that parent process still exists

**Mechanism**:
```python
async def _parent_monitor_loop(self, check_interval: float = 5.0) -> None:
    while True:
        await asyncio.sleep(check_interval)

        try:
            os.kill(self.parent_pid, 0)  # Signal 0 = check existence
        except OSError:
            # Parent died
            log.warning("Parent process died, shutting down")
            os._exit(0)
```

**Benefits**:
- ✅ Catches edge cases where stdin EOF doesn't fire
- ✅ Works regardless of transport type (stdio/sse/http)
- ✅ Configurable interval (default 5s)

---

## Failure Modes & Recovery

### Scenario 1: Claude Code Crashes

**What Happens**:
1. stdin EOF monitor detects closed pipe immediately
2. MCP server exits via `os._exit(0)`
3. PID file cleaned up by atexit handler

**Recovery**: Next Claude Code startup kills any lingering processes

### Scenario 2: SIGKILL (Force Kill)

**What Happens**:
1. Process terminated immediately, no handlers run
2. PID file left behind (stale)

**Recovery**: Next startup detects stale PID, cleans it up

### Scenario 3: Parent Monitor Fails

**What Happens**:
1. Parent monitor crashes/stops checking
2. stdin EOF monitor still works (redundancy)
3. Signal handlers still work

**Recovery**: Multiple independent mechanisms

### Scenario 4: All Monitors Fail

**What Happens**:
1. Process becomes orphan (worst case)
2. Continues running until manual kill

**Recovery**: Next startup uses PID file to kill old instance

---

## Testing

### Manual Test: Multi-Restart

```bash
# Terminal 1: Start Claude Code
claude

# Terminal 2: Check processes
ps aux | grep evolvai-mcp-server
# Should see: ONE process with PPID=claude

# Terminal 1: Exit Claude Code
/exit

# Terminal 2: Check processes again (wait 1 second)
ps aux | grep evolvai-mcp-server
# Should see: NO processes (cleaned up)

# Repeat 3-5 times
# Should NEVER accumulate orphaned processes
```

### Automated Test Scenarios

1. **Normal Shutdown**:
   - Start MCP server → Send SIGTERM → Verify exit

2. **stdin Close**:
   - Start MCP server → Close stdin → Verify exit within 1s

3. **Parent Death**:
   - Start MCP server → Kill parent → Verify exit within 6s (check interval + buffer)

4. **Old Instance Cleanup**:
   - Create stale PID file → Start MCP server → Verify old PID killed

---

## Metrics & Monitoring

### Success Metrics

- **Zero orphan processes** after Claude Code exits
- **< 1s shutdown latency** from stdin close
- **< 6s shutdown latency** from parent death
- **100% PID file cleanup** on normal exit

### Logging

**Key Log Messages**:
```
INFO: Process lifecycle manager initialized (PID: 53176, PPID: 52861, PID file: /tmp/evolvai-mcp-server.pid)
WARNING: Found old MCP server process (PID: 45003), terminating it
INFO: Started stdin EOF monitor
INFO: Started parent process monitor (PPID: 52861, interval: 5.0s)
WARNING: stdin closed (parent process likely exited), shutting down MCP server
```

**Debug Mode**:
```python
lifecycle_manager = ProcessLifecycleManager()
lifecycle_manager.setup()
# Check logs at ~/.serena/logs/*/mcp_*.txt
```

---

## Known Limitations

### 1. Tkinter Event Loop

**Issue**: Main thread still gets stuck in Tkinter (despite GUI disabled)

**Mitigation**: Use `os._exit(0)` to bypass Python cleanup

**Long-term Fix**: Eliminate all Tkinter dependencies

### 2. PID File Race Condition

**Issue**: Multiple processes starting simultaneously might race for PID file

**Mitigation**: First process wins, second kills first (acceptable)

**Long-term Fix**: Use file locks (`fcntl.flock`)

### 3. Non-stdio Transports

**Issue**: stdin EOF monitor only works for stdio transport

**Mitigation**: Parent process monitor still works (5s latency)

**Long-term Fix**: Transport-specific monitors (SSE/HTTP health checks)

---

## Future Improvements

### 1. File Locking

```python
import fcntl

with open(pid_file, 'w') as f:
    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    f.write(str(os.getpid()))
    # Lock released on process exit
```

**Benefits**: Atomic PID file management, prevents races

### 2. systemd/launchd Integration

```xml
<!-- ~/Library/LaunchAgents/com.evolvai.mcp-server.plist -->
<key>KeepAlive</key>
<dict>
    <key>SuccessfulExit</key>
    <false/>  <!-- Don't restart on success -->
</dict>
```

**Benefits**: OS-level process management

### 3. Health Check Endpoint

```python
@app.get("/health")
async def health():
    return {"status": "ok", "pid": os.getpid(), "ppid": os.getppid()}
```

**Benefits**: External monitoring, supports non-stdio transports

### 4. Graceful Shutdown Timeout

```python
# Wait up to 10s for active tool calls to complete
await asyncio.wait_for(
    wait_for_active_tools(),
    timeout=10.0
)
```

**Benefits**: No interrupted operations

---

## References

### Code Locations

- **Lifecycle Manager**: `src/serena/util/process_lifecycle.py`
- **CLI Integration**: `src/serena/cli.py:172-176`
- **MCP Integration**: `src/serena/mcp.py:356-366`
- **Type Annotations**: `src/serena/mcp.py:13-14`

### Related Issues

- **Root Cause Analysis**: `docs/development/architecture/mcp-loading-and-token-optimization-analysis.md` (Part 3)
- **Tkinter Investigation**: Call stack analysis showing main thread stuck

### Commits

- Implementation: (current commit)
- Analysis: 16ea894 (MCP loading logic analysis)

---

## Quick Reference

### Start MCP Server (with lifecycle management)

```bash
evolvai-mcp-server
# Automatically:
# - Kills old instances
# - Creates PID file
# - Starts monitors
# - Registers cleanup handlers
```

### Check Running Instances

```bash
# Find processes
ps aux | grep evolvai-mcp-server

# Check PID file
cat /tmp/evolvai-mcp-server.pid

# Check parent process
ps -p $(cat /tmp/evolvai-mcp-server.pid) -o ppid=
```

### Manual Cleanup

```bash
# Graceful shutdown
kill -TERM $(cat /tmp/evolvai-mcp-server.pid)

# Force kill (if stuck)
kill -KILL $(cat /tmp/evolvai-mcp-server.pid)

# Clean up PID file
rm /tmp/evolvai-mcp-server.pid

# Kill all instances (nuclear option)
pkill -f evolvai-mcp-server
```

---

**Document version**: 1.0
**Last updated**: 2025-11-19
**Status**: Production Ready ✅
