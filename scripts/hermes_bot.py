#!/usr/bin/env python3
"""
Hermes Agent — Telegram bot for Claude Code + VPS management.

Setup on your VPS:
  pip install python-telegram-bot==20.* psutil
  export TELEGRAM_TOKEN="your-bot-token"
  export ALLOWED_USER_IDS="123456789,987654321"   # your Telegram user ID(s)
  export WORK_DIR="/root"                          # default working directory
  python3 hermes_bot.py

Get your user ID: message @userinfobot on Telegram.
"""

import asyncio
import logging
import os
import re
import shlex
import subprocess
import textwrap
import time
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ── Config ────────────────────────────────────────────────────────────────────

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ALLOWED_IDS = set(
    int(x.strip())
    for x in os.environ.get("ALLOWED_USER_IDS", "").split(",")
    if x.strip().isdigit()
)
WORK_DIR = Path(os.environ.get("WORK_DIR", "/root"))
MAX_MSG = 4000  # Telegram message length cap (leave room for formatting)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

# Per-user state for multi-step commands (e.g. /write awaiting content)
_state: dict[int, dict] = {}

# ── Auth guard ────────────────────────────────────────────────────────────────


def auth(func):
    """Decorator: reject messages from non-allowed users."""
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if ALLOWED_IDS and uid not in ALLOWED_IDS:
            await update.message.reply_text("Not authorized.")
            log.warning("Blocked user %s", uid)
            return
        return await func(update, ctx)
    wrapper.__name__ = func.__name__
    return wrapper


# ── Shell helpers ─────────────────────────────────────────────────────────────


def _run(cmd: str | list, cwd: str | None = None, timeout: int = 60) -> str:
    """Run a shell command, return combined stdout+stderr as string."""
    cwd = cwd or str(WORK_DIR)
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        out = (result.stdout + result.stderr).strip()
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return f"(timed out after {timeout}s)"
    except Exception as exc:
        return f"(error: {exc})"


def _chunks(text: str, size: int = MAX_MSG):
    """Split text into Telegram-safe chunks."""
    for i in range(0, len(text), size):
        yield text[i : i + size]


async def _reply(update: Update, text: str, code: bool = True):
    """Send reply, splitting into multiple messages if needed."""
    for chunk in _chunks(text):
        if code:
            await update.message.reply_text(f"```\n{chunk}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(chunk)


async def _reply_plain(update: Update, text: str):
    await _reply(update, text, code=False)


# ── /start  /help ─────────────────────────────────────────────────────────────

HELP_TEXT = """
*Hermes Agent — Claude Code Commands*

*Claude Code*
/claude `<prompt>` — run Claude Code with a prompt
/ask `<question>` — quick one-shot Claude answer
/fix `<description>` — ask Claude to fix something
/reset — clear Claude session context

*File Operations*
/read `<path>` — print file contents
/ls `[path]` — list directory (default: WORK\\_DIR)
/find `<pattern>` — find files matching pattern
/write `<path>` — start a write; send content as next message
/tail `<path>` `[lines]` — tail a file (default 50 lines)
/mkdir `<path>` — create directory

*Code Tasks*
/run `<command>` — run any shell command
/test `[args]` — run tests (npm test / pytest / cargo test)
/build `[args]` — run build (npm run build / make / cargo build)
/install `<package>` — apt install a package

*Git*
/gitstat — git status
/diff `[file]` — git diff
/log `[n]` — last n commits (default 10)
/commit `<message>` — git add \\-A && git commit
/push `[branch]` — git push origin
/pull `[branch]` — git pull origin
/branch — list branches
/checkout `<branch>` — switch branch
/git `<subcmd>` — run any git subcommand

*VPS & Services*
/vps — system info (CPU, RAM, disk, uptime)
/ps `[filter]` — list processes (optional grep filter)
/logs `<service>` `[lines]` — journalctl logs (default 50)
/svcstatus `<service>` — systemd service status
/restart `<service>` — restart a systemd service
/stop `<service>` — stop a service
/startvc `<service>` — start a service
/nginx — nginx status + config test
/hermes — check Hermes agent process status
/reboot — reboot VPS (asks for confirmation)
/df — disk usage
/top — top 10 CPU/RAM processes

/help — show this message
"""


@auth
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hermes Agent online. Send /help for all commands.", parse_mode=ParseMode.MARKDOWN_V2
    )


@auth
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN_V2)


# ── Claude Code commands ───────────────────────────────────────────────────────


def _claude_cmd(prompt: str, flags: str = "") -> str:
    """Build a claude CLI invocation."""
    safe = shlex.quote(prompt)
    return f"claude {flags} --print {safe}"


@auth
async def cmd_claude(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Run Claude Code with a full prompt."""
    prompt = " ".join(ctx.args)
    if not prompt:
        await update.message.reply_text("Usage: /claude <prompt>")
        return
    await update.message.reply_text("Running Claude Code...")
    out = _run(_claude_cmd(prompt), timeout=120)
    await _reply(update, out, code=False)


@auth
async def cmd_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Quick one-shot Claude question."""
    question = " ".join(ctx.args)
    if not question:
        await update.message.reply_text("Usage: /ask <question>")
        return
    out = _run(_claude_cmd(question, "--model claude-haiku-4-5-20251001"), timeout=60)
    await _reply(update, out, code=False)


@auth
async def cmd_fix(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Ask Claude to fix something."""
    description = " ".join(ctx.args)
    if not description:
        await update.message.reply_text("Usage: /fix <description of what to fix>")
        return
    prompt = f"Fix the following issue and explain what you changed: {description}"
    await update.message.reply_text("Asking Claude to fix...")
    out = _run(_claude_cmd(prompt), timeout=180)
    await _reply(update, out, code=False)


@auth
async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Clear Claude session (no persistent session in --print mode, but clears state)."""
    uid = update.effective_user.id
    _state.pop(uid, None)
    await update.message.reply_text("Session state cleared.")


# ── File operations ────────────────────────────────────────────────────────────


@auth
async def cmd_read(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /read <path>")
        return
    path = Path(ctx.args[0]).expanduser()
    if not path.exists():
        await update.message.reply_text(f"File not found: {path}")
        return
    try:
        text = path.read_text(errors="replace")
        await _reply(update, text[:MAX_MSG * 3])
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


@auth
async def cmd_ls(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    target = Path(ctx.args[0]).expanduser() if ctx.args else WORK_DIR
    out = _run(f"ls -lah {shlex.quote(str(target))}")
    await _reply(update, out)


@auth
async def cmd_find(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /find <pattern>")
        return
    pattern = ctx.args[0]
    out = _run(f"find {shlex.quote(str(WORK_DIR))} -name {shlex.quote(pattern)} 2>/dev/null | head -50")
    await _reply(update, out)


@auth
async def cmd_write(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Start a two-step write: /write <path>, then send content."""
    if not ctx.args:
        await update.message.reply_text("Usage: /write <path>")
        return
    uid = update.effective_user.id
    _state[uid] = {"cmd": "write", "path": ctx.args[0]}
    await update.message.reply_text(
        f"Send the content to write to `{ctx.args[0]}` as your next message.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


@auth
async def cmd_tail(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /tail <path> [lines]")
        return
    path = shlex.quote(ctx.args[0])
    lines = ctx.args[1] if len(ctx.args) > 1 else "50"
    out = _run(f"tail -n {lines} {path}")
    await _reply(update, out)


@auth
async def cmd_mkdir(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /mkdir <path>")
        return
    out = _run(f"mkdir -p {shlex.quote(ctx.args[0])}")
    await _reply(update, out or "Directory created.")


# ── Code tasks ─────────────────────────────────────────────────────────────────


@auth
async def cmd_run(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Run an arbitrary shell command."""
    cmd = " ".join(ctx.args)
    if not cmd:
        await update.message.reply_text("Usage: /run <command>")
        return
    await update.message.reply_text(f"Running: {cmd}")
    out = _run(cmd, timeout=120)
    await _reply(update, out)


@auth
async def cmd_test(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    extra = " ".join(ctx.args)
    # Auto-detect test runner
    if (WORK_DIR / "package.json").exists():
        cmd = f"npm test {extra} -- --passWithNoTests 2>&1 | tail -80"
    elif (WORK_DIR / "pytest.ini").exists() or (WORK_DIR / "setup.py").exists():
        cmd = f"pytest {extra} -x -q 2>&1 | tail -80"
    elif (WORK_DIR / "Cargo.toml").exists():
        cmd = f"cargo test {extra} 2>&1 | tail -80"
    elif (WORK_DIR / "Makefile").exists():
        cmd = f"make test {extra} 2>&1 | tail -80"
    else:
        cmd = f"echo 'No test runner detected. Use /run to specify.'"
    await update.message.reply_text("Running tests...")
    out = _run(cmd, timeout=300)
    await _reply(update, out)


@auth
async def cmd_build(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    extra = " ".join(ctx.args)
    if (WORK_DIR / "package.json").exists():
        cmd = f"npm run build {extra} 2>&1 | tail -80"
    elif (WORK_DIR / "Cargo.toml").exists():
        cmd = f"cargo build {extra} 2>&1 | tail -80"
    elif (WORK_DIR / "Makefile").exists():
        cmd = f"make {extra} 2>&1 | tail -80"
    else:
        cmd = "echo 'No build system detected. Use /run to specify.'"
    await update.message.reply_text("Building...")
    out = _run(cmd, timeout=300)
    await _reply(update, out)


@auth
async def cmd_install(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /install <package>")
        return
    pkg = shlex.quote(ctx.args[0])
    await update.message.reply_text(f"Installing {ctx.args[0]}...")
    out = _run(f"apt-get install -y {pkg} 2>&1 | tail -30", timeout=120)
    await _reply(update, out)


# ── Git ────────────────────────────────────────────────────────────────────────


@auth
async def cmd_gitstat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    out = _run("git status")
    await _reply(update, out)


@auth
async def cmd_diff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    target = ctx.args[0] if ctx.args else ""
    out = _run(f"git diff {target} | head -200")
    await _reply(update, out or "(no diff)")


@auth
async def cmd_log(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = ctx.args[0] if ctx.args else "10"
    out = _run(f"git log --oneline -n {n}")
    await _reply(update, out)


@auth
async def cmd_commit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(ctx.args)
    if not msg:
        await update.message.reply_text("Usage: /commit <message>")
        return
    out = _run(f"git add -A && git commit -m {shlex.quote(msg)}")
    await _reply(update, out)


@auth
async def cmd_push(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    branch = ctx.args[0] if ctx.args else ""
    cmd = f"git push origin {branch}".strip() if branch else "git push"
    await update.message.reply_text("Pushing...")
    out = _run(cmd, timeout=60)
    await _reply(update, out)


@auth
async def cmd_pull(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    branch = ctx.args[0] if ctx.args else ""
    cmd = f"git pull origin {branch}".strip() if branch else "git pull"
    out = _run(cmd, timeout=60)
    await _reply(update, out)


@auth
async def cmd_branch(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    out = _run("git branch -a")
    await _reply(update, out)


@auth
async def cmd_checkout(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /checkout <branch>")
        return
    out = _run(f"git checkout {shlex.quote(ctx.args[0])}")
    await _reply(update, out)


@auth
async def cmd_git(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Run any git subcommand: /git <subcmd> [args...]"""
    if not ctx.args:
        await update.message.reply_text("Usage: /git <subcmd> [args...]")
        return
    subcmd = " ".join(ctx.args)
    out = _run(f"git {subcmd}", timeout=60)
    await _reply(update, out)


# ── VPS & Services ─────────────────────────────────────────────────────────────


@auth
async def cmd_vps(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """System overview: uptime, CPU, RAM, disk."""
    parts = [
        _run("uptime"),
        _run("free -h"),
        _run("df -h /"),
        _run("nproc && cat /proc/cpuinfo | grep 'model name' | head -1"),
    ]
    out = "\n---\n".join(parts)
    await _reply(update, out)


@auth
async def cmd_df(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    out = _run("df -h")
    await _reply(update, out)


@auth
async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    out = _run("ps aux --sort=-%cpu | head -12")
    await _reply(update, out)


@auth
async def cmd_ps(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    filter_str = " ".join(ctx.args)
    if filter_str:
        out = _run(f"ps aux | grep -i {shlex.quote(filter_str)} | grep -v grep")
    else:
        out = _run("ps aux --sort=-%mem | head -25")
    await _reply(update, out or "(no matches)")


@auth
async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /logs <service> [lines]")
        return
    svc = shlex.quote(ctx.args[0])
    lines = ctx.args[1] if len(ctx.args) > 1 else "50"
    out = _run(f"journalctl -u {svc} -n {lines} --no-pager 2>&1")
    await _reply(update, out)


@auth
async def cmd_svcstatus(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /svcstatus <service>")
        return
    svc = shlex.quote(ctx.args[0])
    out = _run(f"systemctl status {svc} --no-pager 2>&1 | head -40")
    await _reply(update, out)


@auth
async def cmd_restart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /restart <service>")
        return
    svc = shlex.quote(ctx.args[0])
    out = _run(f"systemctl restart {svc} && systemctl status {svc} --no-pager | head -15")
    await _reply(update, out)


@auth
async def cmd_stop_svc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /stop <service>")
        return
    svc = shlex.quote(ctx.args[0])
    out = _run(f"systemctl stop {svc}")
    await _reply(update, out or f"Stopped {ctx.args[0]}.")


@auth
async def cmd_start_svc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /startvc <service>")
        return
    svc = shlex.quote(ctx.args[0])
    out = _run(f"systemctl start {svc} && systemctl status {svc} --no-pager | head -15")
    await _reply(update, out)


@auth
async def cmd_nginx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    status = _run("systemctl status nginx --no-pager | head -20")
    test = _run("nginx -t 2>&1")
    await _reply(update, f"=== Status ===\n{status}\n\n=== Config Test ===\n{test}")


@auth
async def cmd_hermes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Check Hermes agent process and service status."""
    lines = []
    # Check if there's a systemd service named hermes
    svc = _run("systemctl status hermes 2>&1 | head -15")
    lines.append(f"=== hermes service ===\n{svc}")
    # Check for running python bot processes
    procs = _run("ps aux | grep -E 'hermes|telegram|bot' | grep -v grep")
    lines.append(f"\n=== Matching processes ===\n{procs or '(none found)'}")
    # Check for a hermes log file in common locations
    log_locations = ["/var/log/hermes.log", "/root/hermes.log", "/home/hermes/hermes.log"]
    for loc in log_locations:
        if Path(loc).exists():
            tail = _run(f"tail -20 {shlex.quote(loc)}")
            lines.append(f"\n=== {loc} (last 20 lines) ===\n{tail}")
            break
    await _reply(update, "\n".join(lines))


_reboot_confirm: dict[int, float] = {}

@auth
async def cmd_reboot(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    last = _reboot_confirm.get(uid, 0)
    if time.time() - last < 30:
        await update.message.reply_text("Rebooting VPS now...")
        _run("reboot")
    else:
        _reboot_confirm[uid] = time.time()
        await update.message.reply_text(
            "Send /reboot again within 30 seconds to confirm VPS reboot."
        )


# ── Multi-step message handler ────────────────────────────────────────────────


@auth
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = _state.pop(uid, None)
    if state is None:
        await update.message.reply_text(
            "Unknown command. Send /help for a list of commands."
        )
        return

    if state["cmd"] == "write":
        path = Path(state["path"]).expanduser()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(update.message.text)
            await update.message.reply_text(f"Written to {path} ({len(update.message.text)} bytes).")
        except Exception as e:
            await update.message.reply_text(f"Error writing file: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────


def main():
    if not TOKEN:
        raise SystemExit("Set TELEGRAM_TOKEN environment variable.")
    if not ALLOWED_IDS:
        log.warning("ALLOWED_USER_IDS not set — bot is open to everyone!")

    app = Application.builder().token(TOKEN).build()

    handlers = [
        # Info
        ("start", cmd_start),
        ("help", cmd_help),
        # Claude Code
        ("claude", cmd_claude),
        ("ask", cmd_ask),
        ("fix", cmd_fix),
        ("reset", cmd_reset),
        # Files
        ("read", cmd_read),
        ("ls", cmd_ls),
        ("find", cmd_find),
        ("write", cmd_write),
        ("tail", cmd_tail),
        ("mkdir", cmd_mkdir),
        # Code
        ("run", cmd_run),
        ("test", cmd_test),
        ("build", cmd_build),
        ("install", cmd_install),
        # Git
        ("gitstat", cmd_gitstat),
        ("diff", cmd_diff),
        ("log", cmd_log),
        ("commit", cmd_commit),
        ("push", cmd_push),
        ("pull", cmd_pull),
        ("branch", cmd_branch),
        ("checkout", cmd_checkout),
        ("git", cmd_git),
        # VPS
        ("vps", cmd_vps),
        ("df", cmd_df),
        ("top", cmd_top),
        ("ps", cmd_ps),
        ("logs", cmd_logs),
        ("svcstatus", cmd_svcstatus),
        ("restart", cmd_restart),
        ("stop", cmd_stop_svc),
        ("startvc", cmd_start_svc),
        ("nginx", cmd_nginx),
        ("hermes", cmd_hermes),
        ("reboot", cmd_reboot),
    ]

    for name, handler in handlers:
        app.add_handler(CommandHandler(name, handler))

    # Catch plain text for multi-step commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log.info("Hermes Agent starting (work dir: %s)", WORK_DIR)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
