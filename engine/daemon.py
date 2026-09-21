"""
TubePulse US - 24/7 Fully Autonomous Autopilot Daemon
Continuously runs in the background. Discovers topics, renders videos with the
20-25yo voice and Casually Explained animations, generates thumbnails, creates SEO,
and schedules/publishes to YouTube without any manual clicks or intervention.
"""

import os
import time
import json
import logging
import threading
from datetime import datetime, timezone
from engine.autopilot_engine import run_autonomous_cycle, load_channel_state, advance_channel_day
from engine.youtube_uploader import upload_video_to_youtube

logger = logging.getLogger("TubePulseDaemon")
logging.basicConfig(level=logging.INFO)

DAEMON_STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "media", "daemon_state.json")

# Default daemon configuration
DAEMON_CONFIG = {
    "running": True,
    "mode": "interval", # 'interval' or 'scheduled'
    "interval_minutes": 60, # Runs automatically every 60 minutes (can be adjusted)
    "last_run": None,
    "next_run": None,
    "total_autonomous_runs": 0,
    "auto_upload_enabled": True
}

_daemon_thread = None
_stop_event = threading.Event()

def load_daemon_state() -> dict:
    if os.path.exists(DAEMON_STATE_FILE):
        try:
            with open(DAEMON_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DAEMON_CONFIG.copy()

def save_daemon_state(state: dict):
    os.makedirs(os.path.dirname(DAEMON_STATE_FILE), exist_ok=True)
    with open(DAEMON_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run_daemon_step():
    """Executes a single autonomous production step."""
    logger.info("🤖 [AUTOPILOT DAEMON] Starting hands-off production cycle...")
    try:
        # 1. Run the autonomous cycle (discovers topic, generates script, renders video & thumb)
        cycle_res = run_autonomous_cycle()
        phase = cycle_res.get("phase", "UNKNOWN")
        day = cycle_res.get("day", 1)
        items = cycle_res.get("items_created", [])

        logger.info(f"✓ [AUTOPILOT DAEMON] Day {day} ({phase}): Produced {len(items)} video(s) autonomously.")

        # 2. Update daemon state
        d_state = load_daemon_state()
        d_state["last_run"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        d_state["total_autonomous_runs"] = d_state.get("total_autonomous_runs", 0) + 1
        
        # Calculate next run timestamp
        interval_secs = d_state.get("interval_minutes", 60) * 60
        next_ts = time.time() + interval_secs
        d_state["next_run"] = datetime.fromtimestamp(next_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        save_daemon_state(d_state)

        return cycle_res
    except Exception as e:
        logger.error(f"Error during autonomous daemon step: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

def _daemon_loop(check_interval_seconds: int = 15):
    """Continuous background loop running in a dedicated thread."""
    logger.info("🚀 Autonomous Autopilot Daemon thread started!")
    save_daemon_state(load_daemon_state())

    while not _stop_event.is_set():
        try:
            d_state = load_daemon_state()
            c_state = load_channel_state()

            if d_state.get("running") and c_state.get("autopilot_enabled", True):
                last_run_str = d_state.get("last_run")
                should_run = False

                if not last_run_str:
                    # Never run before -> run immediately
                    should_run = True
                else:
                    # Check if interval has passed
                    try:
                        last_dt = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
                        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                        interval_secs = d_state.get("interval_minutes", 60) * 60
                        if elapsed >= interval_secs:
                            should_run = True
                    except Exception:
                        should_run = True

                if should_run:
                    run_daemon_step()

        except Exception as err:
            logger.error(f"Daemon loop encountered exception: {err}")

        # Sleep check interval
        for _ in range(check_interval_seconds):
            if _stop_event.is_set():
                break
            time.sleep(1)

def start_autopilot_daemon(interval_minutes: int = 60):
    """Starts the 24/7 autonomous background daemon thread."""
    global _daemon_thread, _stop_event
    if _daemon_thread and _daemon_thread.is_alive():
        logger.info("Autopilot daemon thread is already running.")
        return True

    _stop_event.clear()
    d_state = load_daemon_state()
    d_state["running"] = True
    d_state["interval_minutes"] = interval_minutes
    save_daemon_state(d_state)

    _daemon_thread = threading.Thread(target=_daemon_loop, daemon=True, name="TubePulseAutopilotDaemon")
    _daemon_thread.start()
    logger.info(f"Autopilot daemon successfully launched with {interval_minutes}m interval.")
    return True

def stop_autopilot_daemon():
    """Pauses the 24/7 autonomous background daemon thread."""
    global _stop_event
    _stop_event.set()
    d_state = load_daemon_state()
    d_state["running"] = False
    save_daemon_state(d_state)
    logger.info("Autopilot daemon paused.")
    return True

if __name__ == "__main__":
    print("="*60)
    print("🤖 TubePulse US - Starting Standalone Autopilot Daemon")
    print("="*60)
    start_autopilot_daemon(interval_minutes=60)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_autopilot_daemon()
        print("Daemon stopped.")
