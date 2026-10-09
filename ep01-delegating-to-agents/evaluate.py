"""Independent novelty evaluation using delivered reports, not discovery state."""
import argparse
import json
from pathlib import Path
import unicodedata


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if c.isalnum())


def identity_keys(lead):
    keys = set()
    if lead.get('id'):
        keys.add('show:' + str(lead['id']))
    publisher = normalize(lead.get('host_or_publisher', ''))
    if publisher:
        keys.add('publisher:' + publisher)
    email = lead.get('public_email', '').strip().casefold()
    if email:
        keys.add('email:' + email)
    return keys


def evaluate(report, earlier_reports, minimum_new=5):
    prior_keys = set()
    prior_shows = set()
    for previous in earlier_reports:
        for lead in previous['leads']:
            prior_keys.update(identity_keys(lead))
            prior_shows.add(str(lead.get('id', '')))
    repeats, new_proxies, new_shows, unknown = [], 0, 0, 0
    checked_keys = set(prior_keys)
    checked_shows = set(prior_shows)
    for lead in report['leads']:
        keys = identity_keys(lead)
        contact_keys = {key for key in keys if not key.startswith('show:')}
        if not contact_keys:
            unknown += 1
        overlap = keys & checked_keys
        if overlap:
            repeats.append({'show': lead['show'], 'matched_keys': sorted(overlap)})
        elif contact_keys:
            new_proxies += 1
        show_id = str(lead.get('id', ''))
        if show_id and show_id not in checked_shows:
            new_shows += 1
        checked_shows.add(show_id)
        checked_keys.update(keys)
    count = len(report['leads'])
    passed = new_proxies >= minimum_new and not repeats and unknown == 0
    return {
        'passed': passed, 'minimum_new_host_or_publisher_proxies': minimum_new,
        'delivered': count, 'new_shows': new_shows,
        'new_host_or_publisher_proxies': new_proxies,
        'repeat_count': len(repeats), 'repeats': repeats,
        'missing_contact_identity': unknown,
        'novelty_rate': new_proxies / count if count else None,
        'history_runs_checked': len(earlier_reports),
        'identity_limit': 'Directory host/publisher labels and public emails are proxies, not verified individual people. Aliases and co-host changes may evade matching; shared publishers may suppress distinct hosts.',
        'reply_rate': None,
        'reply_rate_status': 'Not measured; outreach has not started',
    }


def earlier_reports(report, history):
    reports = []
    for path in history.glob('*.json'):
        if path.name.endswith('.eval.json'):
            continue
        previous = json.loads(path.read_text())
        if 'leads' in previous and previous['run_at'] < report['run_at']:
            reports.append(previous)
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    parser.add_argument('--history', type=Path, default=Path(__file__).resolve().parent / 'reports')
    parser.add_argument('--minimum-new', type=int, default=5)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    result = evaluate(report, earlier_reports(report, args.history), args.minimum_new)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
