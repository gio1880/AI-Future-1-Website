"""Saves every robot run as a CSV file and rebuilds the dashboard.

Where the runs come from:
  1. VS Code's "Pybricks" output panel. VS Code keeps a copy of it in its log folder; this script reads
     that copy, so students just run their program as usual ("Compile and Start Program").
  2. robot-data/inbox/*.txt - output pasted by hand (for example from code.pybricks.com). Processed
     files move to inbox/done/.

Usage (VS Code starts the first one by itself when the folder opens - see .vscode/tasks.json):
  python collect_runs.py --watch    keep running, save each run a few seconds after it ends
  python collect_runs.py            one pass: save new runs, rebuild the dashboard
  python collect_runs.py --open     one pass, then open the dashboard

Nothing here talks to the robot. Only the standard library is used.
"""
import csv
import glob
import hashlib
import json
import os
import re
import sys
import time
import webbrowser
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(HERE, "runs")
INBOX_DIR = os.path.join(HERE, "inbox")
INDEX_FILE = os.path.join(RUNS_DIR, "runs.json")
STATE_FILE = os.path.join(RUNS_DIR, ".collected.json")
LOCK_FILE = os.path.join(HERE, ".watch.lock")
TEMPLATE = os.path.join(HERE, "dashboard_template.html")
DASHBOARD = os.path.join(HERE, "dashboard.html")
ROBOT_MASTER = os.path.join(HERE, "..", "robot_master.py")

IDLE_S = 30  # a run with no end line is saved once its log has been quiet this long
POLL_S = 2
# robot_master.py settings shown on the dashboard and used by the tuning tips
SETTINGS = ["WHEEL_MM", "TW", "DRIVE_V", "DRIVE_A", "DRIVE_KH", "DRIVE_KW", "DRIVE_KS", "DRIVE_MOTOR_ACC",
            "TURN_RATE", "TURN_ACC", "TURN_KT", "ARM_KP_X", "ARM_KI_X", "ARM_KD_X", "ARM_TIMEOUT_EXTRA_MS",
            "SQUARE_SPEED", "SQUARE_TORQUE", "BATTERY_WARN_MV"]


# ------------------------------------------------------------------ sources
def vscode_logs():
    """Every '*-Pybricks.log' copy of the VS Code output panel (Windows, macOS, Linux; stable + Insiders)."""
    roots = []
    if os.environ.get("APPDATA"):
        roots.append(os.environ["APPDATA"])
    home = os.path.expanduser("~")
    roots += [os.path.join(home, "Library", "Application Support"), os.path.join(home, ".config")]
    found = []
    for root in roots:
        for app in ("Code", "Code - Insiders", "VSCodium"):
            found += glob.glob(os.path.join(root, app, "logs", "*", "window*", "exthost", "output_logging_*",
                                           "*-Pybricks.log"))
    return found


def inbox_files():
    os.makedirs(INBOX_DIR, exist_ok=True)
    return glob.glob(os.path.join(INBOX_DIR, "*.txt"))


# ------------------------------------------------------------------ parsing
RE_BATTERY = re.compile(r"battery(?: low)? (\d+) ?mV")


def parse_runs(lines):
    """Splits program output into runs. Each run: header, rows, name, battery, status, notes, summary.
    'open' runs (no end line yet) are returned with status None."""
    runs = []
    cur = None
    pending = {"name": "", "battery": None, "notes": []}

    def close(status):
        nonlocal cur
        if cur is not None:
            if status == "ended (no summary)" and cur.get("done"):
                status = "finished"  # printed DONE, just no LOG_END (older code or no finish())
            cur["status"] = status
            runs.append(cur)
            cur = None

    for i, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        s = line.strip()
        if not s:
            continue
        m = RE_BATTERY.search(s)
        if m and not s.startswith("SUMMARY"):
            pending["battery"] = int(m.group(1))
            if cur is not None and cur["battery"] is None:
                cur["battery"] = pending["battery"]
        if s.startswith("LOG_NAME,"):
            if cur is not None:
                close("ended (no summary)")
            pending["name"] = s[len("LOG_NAME,"):].strip()
            continue
        if s.startswith("LOG,step,"):
            if cur is not None:
                close("ended (no summary)")
            cur = {"line": i, "header": s.split(",")[1:], "rows": [], "name": pending["name"],
                   "battery": pending["battery"], "notes": pending["notes"], "summary": [], "status": None,
                   "done": False}
            pending = {"name": "", "battery": None, "notes": []}
            continue
        if cur is None:
            # warnings from the start of a program (battery, gyro zero) belong to the run that follows
            if s.startswith(("WARNING", "NOTE:", "HOME FAILED", "STOP:")):
                pending["notes"] = (pending["notes"] + [s])[-5:]
            elif s.startswith(("The program was stopped", "Traceback")):
                pending = {"name": "", "battery": None, "notes": []}
            continue
        if s.startswith("LOG,"):
            parts = s.split(",")[1:]
            if parts and parts[0].isdigit():
                cur["rows"].append(parts)
        elif s.startswith("SUMMARY"):
            cur["summary"].append(s[len("SUMMARY"):].strip())
        elif s == "LOG_END" or s.startswith("SETUP DONE"):
            close("finished")  # SETUP DONE = arm_setup.py, which has no finish()
        elif s.startswith("SETUP STOP"):
            cur["notes"].append(s)
            close("stopped by arm_setup (see note)")
        elif s.startswith("The program was stopped"):
            close("stopped with the button")
        elif s.startswith("Traceback"):
            err = ""
            for nxt in lines[i + 1:i + 12]:
                n = nxt.strip()
                if re.match(r"^\w*(Error|Exception|Interrupt)\b", n) or n.startswith("OSError"):
                    err = n
                    break
            cur["notes"].append("Program error: " + (err or "see the Pybricks output"))
            close("error")
        elif s.startswith(("ABORT", "ARM TIMEOUT", "SQUARE FAILED", "HOME FAILED", "STOP:", "WARNING")):
            cur["notes"].append(s)
            if s.startswith("ABORT"):
                close("aborted (safety stop)")
        elif s.startswith("DONE"):
            cur["done"] = True  # run files that don't call finish() end here; LOG_END never comes
    if cur is not None:
        runs.append(cur)  # still open
    return runs


# ------------------------------------------------------------------ saving
def lp(path):
    """Windows long-path form, so deep folders (this one is ~200 characters) never hit the 260 limit."""
    path = os.path.abspath(path)
    if os.name == "nt" and not path.startswith("\\\\?\\"):
        return "\\\\?\\" + path
    return path


def load_json(path, default):
    try:
        with open(lp(path), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(lp(tmp), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    os.replace(lp(tmp), lp(path))


def run_key(source, run):
    first = ",".join(run["rows"][0]) if run["rows"] else ""
    h = hashlib.sha1((source + "|" + str(run["line"]) + "|" + first).encode("utf-8")).hexdigest()[:16]
    return h


def slug(name):
    s = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")
    return s[:24].strip("-") or "run"


def auto_name(run):
    """Name for a run without start("name"): its first four moves (without numbers), so the same program
    groups together even while students change its numbers."""
    moves = []
    for r in run["rows"]:
        cmd = r[1] if len(r) > 2 else ""
        if cmd in ("drive", "turn") or cmd.startswith("arm:"):
            if cmd.startswith("arm:") and not moves and r[0] in ("1", "2"):
                continue  # the homing park move at the start is the same in every run
            moves.append("left arm" if cmd == "arm:left_arm" else "right arm" if cmd == "arm:right_arm" else cmd)
        if len(moves) == 4:
            break
    return "Unnamed: " + ", ".join(moves) if moves else "Unnamed run"


def save_run(run, when, source_kind, exact=True):
    os.makedirs(RUNS_DIR, exist_ok=True)
    name = run["name"] or auto_name(run)
    base = when.strftime("%Y-%m-%d_%H%M%S") + "_" + slug(name)
    path = os.path.join(RUNS_DIR, base + ".csv")
    n = 2
    while os.path.exists(lp(path)):
        path = os.path.join(RUNS_DIR, base + "_" + str(n) + ".csv")
        n += 1
    with open(lp(path), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(run["header"])
        for r in run["rows"]:
            w.writerow(r)
    index = load_json(INDEX_FILE, [])
    meta = {"id": os.path.splitext(os.path.basename(path))[0], "file": os.path.basename(path), "name": name,
            "time": when.strftime("%Y-%m-%d %H:%M:%S"), "time_exact": exact, "seq": len(index),
            "battery": run["battery"], "status": run["status"], "notes": run["notes"], "summary": run["summary"],
            "moves": len(run["rows"]), "source": source_kind}
    index.append(meta)
    save_json(INDEX_FILE, index)
    return meta


def collect(verbose=True):
    """One pass over all sources. Returns the list of runs saved."""
    os.makedirs(RUNS_DIR, exist_ok=True)
    state = load_json(STATE_FILE, {"keys": []})
    seen = set(state["keys"])
    saved = []
    now = time.time()
    for kind, files in (("vscode", vscode_logs()), ("pasted", inbox_files())):
        for path in files:
            try:
                mtime = os.path.getmtime(path)
                with open(path, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except OSError:
                continue
            all_done = True
            for run in parse_runs(lines):
                if not run["rows"]:
                    continue
                key = run_key(path, run)
                if key in seen:
                    continue
                if run["status"] is None:
                    if kind == "vscode" and now - mtime < IDLE_S:
                        all_done = False
                        continue  # still running (or just finished without an end line): wait
                    run["status"] = "finished" if run.get("done") else \
                        "no end line (program still running or output cut off)"
                # A run seen while it happens gets the current time. Runs found later in an older log only
                # get the log's last-change time, marked approximate (they stay in log order via "seq").
                live = now - mtime < 60
                when = datetime.now() if live else datetime.fromtimestamp(mtime)
                meta = save_run(run, when, kind, exact=live)
                seen.add(key)
                state["keys"] = sorted(seen)
                save_json(STATE_FILE, state)  # after every run, so a crash later can't save it twice
                saved.append(meta)
                if verbose:
                    print("Saved:", meta["name"], "|", meta["moves"], "moves |", meta["status"], "|", meta["file"])
            if kind == "pasted" and all_done:
                done = os.path.join(INBOX_DIR, "done")
                os.makedirs(done, exist_ok=True)
                try:
                    os.replace(path, os.path.join(done, os.path.basename(path)))
                except OSError:
                    pass
    state["keys"] = sorted(seen)
    save_json(STATE_FILE, state)
    return saved


# ------------------------------------------------------------------ dashboard
def read_settings():
    vals = {}
    try:
        with open(lp(ROBOT_MASTER), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return vals
    for name in SETTINGS:
        m = re.search(r"^" + name + r"\s*=\s*([-0-9.]+|None)", text, re.M)
        if m:
            v = m.group(1)
            vals[name] = None if v == "None" else float(v)
    return vals


def build_dashboard():
    index = load_json(INDEX_FILE, [])
    runs = []
    for meta in index:
        path = os.path.join(RUNS_DIR, meta["file"])
        if not os.path.exists(lp(path)):
            continue  # CSV deleted on purpose: drop it from the dashboard
        with open(lp(path), newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        r = dict(meta)
        r["header"] = rows[0]
        r["rows"] = rows[1:]
        runs.append(r)
    data = {"built": datetime.now().strftime("%Y-%m-%d %H:%M"), "runs": runs, "settings": read_settings()}
    with open(lp(TEMPLATE), encoding="utf-8") as f:
        html = f.read()
    blob = json.dumps(data).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", blob)
    tmp = DASHBOARD + ".tmp"
    with open(lp(tmp), "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(lp(tmp), lp(DASHBOARD))
    return len(runs)


# ------------------------------------------------------------------ watch mode
def other_watcher_alive():
    try:
        with open(LOCK_FILE) as f:
            beat = float(f.read().strip() or 0)
        return time.time() - beat < 3 * POLL_S + 5
    except (OSError, ValueError):
        return False


def watch():
    if other_watcher_alive():
        print("Robot data saver is already running in another window. Nothing to do here.")
        return
    print("Robot data saver is ON. Run your program as usual - each run is saved to robot-data\\runs\\")
    print("Dashboard:", DASHBOARD)
    collect()
    build_dashboard()
    while True:
        try:
            with open(LOCK_FILE, "w") as f:
                f.write(str(time.time()))
            if collect():
                n = build_dashboard()
                print("Dashboard updated (" + str(n) + " runs). Open robot-data\\dashboard.html or refresh it.")
        except Exception as e:  # keep watching even if one log file is odd
            print("Problem while saving runs:", e)
        time.sleep(POLL_S)


if __name__ == "__main__":
    if "--watch" in sys.argv:
        try:
            watch()
        except KeyboardInterrupt:
            pass
    else:
        new = collect()
        n = build_dashboard()
        print(len(new), "new run(s) saved,", n, "run(s) on the dashboard:", DASHBOARD)
        if "--open" in sys.argv:
            webbrowser.open("file:///" + DASHBOARD.replace("\\", "/"))
