"""Run weekly workspace reports while this cloud instance is running."""
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
ANCHOR = datetime(1970, 1, 5, 14, tzinfo=timezone.utc).timestamp()
WEEK = 7 * 24 * 60 * 60


def cycle(timestamp):
    return int((timestamp - ANCHOR) // WEEK)


def tick():
    path = ROOT / 'state/schedule.json'
    state = json.loads(path.read_text()) if path.exists() else {}
    current = cycle(time.time())
    if state.get('last_successful_cycle', -1) >= current:
        return False
    subprocess.run([sys.executable, str(ROOT / 'prospect.py')], cwd=ROOT, check=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'last_successful_cycle': current}, indent=2))
    temporary.replace(path)
    return True


if __name__ == '__main__':
    (ROOT / 'state').mkdir(exist_ok=True)
    with (ROOT / 'state/scheduler.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit('A workspace scheduler is already running')
        while True:
            try:
                ran = tick()
                if ran:
                    print('Weekly report saved', flush=True)
            except Exception as exc:
                print(f'Weekly run failed; retry in one hour: {exc}', file=sys.stderr, flush=True)
                if '--once' in sys.argv:
                    sys.exit(1)
                time.sleep(3600)
                continue
            if '--once' in sys.argv:
                break
            time.sleep(60)
