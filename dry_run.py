"""Capture a live source snapshot, then simulate weekly runs in isolated state."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from evaluate import evaluate
import prospect
import schedule


def live_history_hashes():
    return {str(path.relative_to(prospect.ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for folder in ('state', 'reports')
            for path in (prospect.ROOT / folder).rglob('*') if path.is_file()}


def main():
    profile = json.loads((prospect.ROOT / 'profile.json').read_text())
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    root = prospect.ROOT / 'dry-runs' / stamp
    reports = root / 'reports'
    (root / 'state').mkdir(parents=True)
    (root / 'sources').mkdir()
    before = live_history_hashes()
    original_fetch = prospect.fetch
    sources = {}
    replay = False

    def snapshot_fetch(url):
        if url in sources:
            entry = sources[url]
            if entry.get('error'):
                raise OSError(entry['error'])
            return (root / entry['file']).read_bytes()
        if replay:
            raise RuntimeError('Replay attempted a URL outside the recorded snapshot')
        try:
            data = original_fetch(url)
            relative = 'sources/' + hashlib.sha256(url.encode()).hexdigest() + '.bin'
            (root / relative).write_bytes(data)
            sources[url] = {'file': relative, 'sha256': hashlib.sha256(data).hexdigest()}
            return data
        except Exception as exc:
            sources[url] = {'error': str(exc)}
            raise

    def execute_discovery(*args, **kwargs):
        prospect.run(profile, reports, root / 'state/delivered.json')

    steps = []
    simulated_time = datetime(2026, 10, 12, 14, tzinfo=timezone.utc).timestamp()
    with patch.object(prospect, 'fetch', side_effect=snapshot_fetch), patch.object(schedule, 'ROOT', root), patch.object(schedule.subprocess, 'run', side_effect=execute_discovery):
        for label, offset in [('first_due_run', 0), ('same_week_second_tick', 60), ('next_week_same_sources', schedule.WEEK), ('third_week_same_sources', 2 * schedule.WEEK)]:
            with patch.object(schedule.time, 'time', return_value=simulated_time + offset):
                ran = schedule.tick()
            step = {'scenario': label, 'simulated_due_at': datetime.fromtimestamp(simulated_time + offset, timezone.utc).isoformat(), 'discovery_executed': ran}
            if ran:
                report_path = sorted(reports.glob('*.json'))[-1]
                report = json.loads(report_path.read_text())
                step.update(report=str(report_path.relative_to(root)), discovered=report['discovered'], delivered=report['new_delivered'], blocked_repeats=report['blocked_repeats'], eval=report['eval'])
            steps.append(step)
            replay = True
    first_report = json.loads((root / steps[0]['report']).read_text())
    first = first_report['leads'][0] if first_report['leads'] else None
    injected_eval = None
    if first:
        duplicate = dict(first, id='synthetic-new-show-id', show='Synthetic second show from existing publisher')
        injected_eval = evaluate({'leads': [duplicate]}, [first_report], minimum_new=1)
    unchanged = before == live_history_hashes()
    outcomes = {
        'baseline_meets_target': steps[0].get('eval', {}).get('passed', False),
        'scheduler_skips_second_tick_in_same_week': not steps[1]['discovery_executed'],
        'scheduler_runs_in_next_week': steps[2]['discovery_executed'],
        'no_repeats_across_simulated_deliveries': all(step.get('eval', {}).get('repeat_count', 0) == 0 for step in steps),
        'eval_rejects_new_show_from_existing_publisher': bool(injected_eval) and injected_eval['repeat_count'] == 1 and not injected_eval['passed'],
        'live_history_unchanged': unchanged,
    }
    result = {'run_at': datetime.now(timezone.utc).isoformat(), 'mode': 'First discovery uses live public sources; later weeks replay that same snapshot. Weekly clock is simulated; report timestamps are actual execution times.',
              'profile': profile, 'steps': steps, 'injected_duplicate_eval': injected_eval,
              'checks': outcomes, 'mechanics_passed': all(outcomes.values()),
              'source_requests': len(sources), 'source_failures': sum('error' in item for item in sources.values()),
              'limitations': ['A fixed source snapshot cannot demonstrate sustained weekly lead supply.', 'Host/publisher labels are identity proxies, not verified people.', 'ICP precision, deliverability, and replies are not measured.', 'Scheduler subprocess dispatch is replaced by the real discovery function with isolated paths; process lifecycle is not tested here.']}
    (root / 'source-manifest.json').write_text(json.dumps(sources, indent=2))
    (root / 'result.json').write_text(json.dumps(result, indent=2))
    lines = ['# Podcast prospecting dry run', '', result['mode'], '', '| Scenario | Delivered | Repeats | Novelty eval |', '|---|---:|---:|---|']
    for step in steps:
        lines.append(f"| {step['scenario']} | {step.get('delivered', 'skipped')} | {step.get('eval', {}).get('repeat_count', '—')} | {('PASS' if step['eval']['passed'] else 'FAIL') if 'eval' in step else 'not run'} |")
    lines.extend(['', '## Mechanics checks', ''])
    lines.extend(f"- {'PASS' if ok else 'FAIL'}: {name}" for name, ok in outcomes.items())
    lines.extend(['', '## Limits', ''] + ['- ' + value for value in result['limitations']])
    (root / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')
    print('Dry-run summary:', root / 'SUMMARY.md')
    print('Mechanics checks:', json.dumps(outcomes))
    if not all(outcomes.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
