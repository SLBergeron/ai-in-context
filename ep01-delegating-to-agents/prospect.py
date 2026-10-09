#!/usr/bin/env python3
"""Discover public podcast candidates; preserve evidence and delivery history."""
import argparse
import csv
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from evaluate import earlier_reports, evaluate, identity_keys

ROOT = Path(__file__).resolve().parent


def fetch(url):
    if urlparse(url).scheme != "https":
        raise ValueError("Source requires HTTPS; not fetched")
    request = Request(url, headers={"User-Agent": "LemonbrandPodcastResearch/0.1"})
    with urlopen(request, timeout=20) as response:
        content = response.read(5_000_001)
        if len(content) > 5_000_000:
            raise ValueError("Source exceeds 5 MB limit")
        return content


def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", value or "")).strip()


def feed_details(url):
    root = ET.fromstring(fetch(url))
    channel = root.find("channel")
    if channel is None:
        raise ValueError("Unsupported feed format; needs manual review")
    items = channel.findall("item")[:10]
    titles = [clean(item.findtext("title")) for item in items]
    dates = []
    for item in items:
        try:
            date = parsedate_to_datetime(item.findtext("pubDate", ""))
            dates.append(date.replace(tzinfo=date.tzinfo or timezone.utc))
        except (ValueError, TypeError):
            pass
    latest = max(dates).isoformat() if dates else ""
    guest_titles = [title for title in titles if re.search(r"\b(with|guest|interview|featuring)\b", title, re.I)]
    email = channel.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}owner/{http://www.itunes.com/dtds/podcast-1.0.dtd}email", "")
    return {
        "description": clean(channel.findtext("description")),
        "website": channel.findtext("link", ""),
        "public_email": email,
        "latest_episode": latest,
        "guest_evidence": " | ".join(guest_titles[:3]),
        "recent_titles": " | ".join(titles[:5]),
    }


def safe_cell(value):
    text = str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@")) else text


def run(profile, output, state_path, allow_unverified=False, limit=25):
    if not profile["positioning_verified"] and not allow_unverified:
        raise ValueError("Lemonbrand positioning is unverified. Review profile.json before scheduling.")
    state = json.loads(state_path.read_text()) if state_path.exists() else {"delivered": []}
    prior_identity_keys = set(state.get('identity_keys', []))
    if output.exists():
        for path in output.glob('*.json'):
            previous = json.loads(path.read_text())
            for lead in previous.get('leads', []):
                prior_identity_keys.update(identity_keys(lead))
    candidates, errors = {}, []
    successful_searches = 0
    for term in profile["search_terms"]:
        query = urlencode({"term": term, "media": "podcast", "entity": "podcast", "limit": limit, "country": profile["country"]})
        source = "https://itunes.apple.com/search?" + query
        try:
            results = json.loads(fetch(source))["results"]
            successful_searches += 1
        except Exception as exc:
            errors.append({"source": source, "error": str(exc)})
            continue
        for item in results:
            identity = str(item.get("collectionId", ""))
            if not identity or identity in candidates:
                continue
            candidates[identity] = {
                "id": identity, "show": item.get("collectionName", ""),
                "host_or_publisher": item.get("artistName", ""),
                "directory_url": item.get("collectionViewUrl", ""),
                "feed_url": item.get("feedUrl", ""), "search_term": term,
                "source": source, "website": "", "public_email": "",
                "latest_episode": "", "guest_evidence": "", "recent_titles": "",
                "description": "", "feed_status": "not checked",
            }
        time.sleep(0.4)
    if successful_searches == 0:
        raise RuntimeError("All discovery requests failed: " + json.dumps(errors))
    now = datetime.now(timezone.utc)
    for row in candidates.values():
        try:
            row.update(feed_details(row["feed_url"]))
            row["feed_status"] = "verified"
        except Exception as exc:
            row["feed_status"] = str(exc)
        text = (row["show"] + " " + row["description"] + " " + row["recent_titles"]).lower()
        matches = [word for word in profile["fit_keywords"] if word.lower() in text]
        active = bool(row["latest_episode"]) and 0 <= (now - datetime.fromisoformat(row["latest_episode"])).days <= profile["max_inactive_days"]
        row["active"] = "yes" if active else "unknown or inactive"
        row["score"] = len(matches) * 10 + (5 if active else 0) + (3 if row["guest_evidence"] else 0)
        row["fit_evidence"] = ", ".join(matches) or "No verified positioning match"
        row['icp_status'] = ('strong candidate' if active and row['guest_evidence'] else 'needs activity/guest verification') if matches else 'outside ICP'
        row["review_status"] = "Candidate; verify audience fit, guest availability, and contact before outreach"
    eligible = [row for row in candidates.values() if row['icp_status'] != 'outside ICP' or allow_unverified]
    eligible.sort(key=lambda row: (-row['score'], row['show']))
    new_rows = []
    blocked_repeats = 0
    selected_keys = set(prior_identity_keys)
    for row in eligible:
        keys = identity_keys(row)
        if row['id'] in state['delivered'] or keys & selected_keys:
            blocked_repeats += 1
            continue
        if len(new_rows) < profile['max_leads']:
            new_rows.append(row)
            selected_keys.update(keys)
    output.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
    fields = ["id", "show", "host_or_publisher", "score", "fit_evidence", "icp_status", "active", "latest_episode", "guest_evidence", "public_email", "website", "directory_url", "feed_url", "feed_status", "review_status", "search_term", "source", "description", "recent_titles"]
    with (output / (stamp + ".csv")).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: safe_cell(row[key]) for key in fields} for row in new_rows)
    summary = {
        "run_at": now.isoformat(), "profile_sha256": hashlib.sha256(json.dumps(profile, sort_keys=True).encode()).hexdigest(),
        "positioning_verified": profile["positioning_verified"], "discovered": len(candidates),
        "new_delivered": len(new_rows), "search_errors": errors,
        "blocked_repeats": blocked_repeats,
        "outside_icp": len(candidates) - len(eligible),
        "feed_verified": sum(row["feed_status"] == "verified" for row in candidates.values()),
        "leads": new_rows,
    }
    summary['eval'] = evaluate(summary, earlier_reports(summary, output), profile.get('minimum_new_per_week', 5))
    (output / (stamp + ".json")).write_text(json.dumps(summary, indent=2))
    lines = ["# Lemonbrand podcast candidates", "", f"New candidates: {len(new_rows)}; discovered: {len(candidates)}.",
             f"Novelty eval: {'PASS' if summary['eval']['passed'] else 'FAIL'}; new host/publisher proxies: {summary['eval']['new_host_or_publisher_proxies']}; repeats: {summary['eval']['repeat_count']}.",
             f"Business positioning verified: {profile['positioning_verified']}.",
             "Guest title patterns are clues, not confirmation that a show accepts pitches.", ""]
    for row in new_rows:
        lines.extend([f"- {row['show']}: score {row['score']}; {row['fit_evidence']}",
                      f"  Directory: {row['directory_url']}", f"  Guest clues: {row['guest_evidence'] or 'not verified'}"])
    (output / (stamp + ".md")).write_text("\n".join(lines) + "\n")
    state["delivered"] = sorted(set(state["delivered"]) | {row["id"] for row in new_rows})
    state['identity_keys'] = sorted(selected_keys)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2))
    temporary.replace(state_path)
    print(json.dumps({key: value for key, value in summary.items() if key != "leads"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=ROOT / "profile.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    parser.add_argument("--state", type=Path, default=ROOT / "state/delivered.json")
    parser.add_argument("--allow-unverified", action="store_true", help="Exploratory run only; no verified business fit")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    try:
        run(json.loads(args.profile.read_text()), args.output, args.state, args.allow_unverified, args.limit)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
