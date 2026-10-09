# Lemonbrand Podcast Prospector

An open-source demo of weekly podcast discovery with an independent novelty eval.
Built for [Lemonbrand](https://lemonbrand.io), which helps small businesses put AI
into everyday operations. Follow along through the code, issues, tests, and eval
methodology. Licensed under [MIT](LICENSE).

## What it does

- Searches Apple's public podcast directory using a configurable business profile.
- Reads public RSS feeds for recent episodes, guest clues, websites, and contacts.
- Ranks candidates and writes CSV, Markdown, and JSON reports locally.
- Suppresses repeated show IDs, normalized host/publisher labels, and public emails.
- Evaluates delivery against earlier reports: at least five new identity proxies
  and zero repeats by default. Empty batches fail the prospecting goal.

The [podcast ICP](ICP.md) prioritizes shows for accounting/tax firm owners and
independent insurance agency owners, followed by small-business operations and
practical AI. Keyword matches are candidate clues, not confirmed audience fit.

## Quick start

Python 3.12+ is required. No third-party packages or API keys are needed.

```sh
cd /path/to/your/checkout
python -m unittest -q
python prospect.py
```

Edit `profile.json` for your business, search terms, keywords, geography, volume,
and novelty target. Verify positioning before setting `positioning_verified`.
The included Lemonbrand profile was researched from its public website.

Reports are saved in `reports/`; delivery history is saved in `state/`.
Retain both across runs. They are ignored by Git and are not included in the
public source repository. Never reset history merely to make the eval pass.
All HTTPS requests retain TLS verification. Cloud users may need to allow
`itunes.apple.com` and the exact hostnames of returned RSS feeds.

## Prove the behavior

```sh
python dry_run.py
python evaluate.py reports/<timestamp>.json --history reports
```

The dry run captures live public sources once, then replays simulated weekly
runs in isolated state under `dry-runs/<timestamp>/`. It records source failures,
checks repeat suppression and same-week scheduler skipping, injects a repeated
publisher, and checks that production history remains unchanged.

The demo baseline delivered 20 then 17 new host/publisher identities with zero
repeats. Once the fixed pool was exhausted, it delivered zero and correctly
failed the novelty goal. Six mechanics checks and ten tests passed. See [ICP.md](ICP.md)
for eval definitions and limitations. Individual prospect data and raw feeds are
kept locally rather than committed as public demo evidence.

## Weekly scheduling

For reports saved directly into your workspace, use an always-on host:

```sh
mkdir -p state
nohup python -u schedule.py >> state/scheduler.log 2>&1 < /dev/null &
```

The schedule is Mondays at 14:00 UTC. The scheduler prevents concurrent instances,
catches up the latest missed weekly cycle, and retries operational failures after
one hour. It runs only while the host is awake. Restart it after a machine restart;
files and history persist, but processes do not. A failed novelty eval is reported
without retrying already delivered prospects indefinitely.

The optional GitHub Actions workflow requires repository variable
`ENABLE_PUBLIC_PROSPECTING=true`. It saves reports and state as Actions artifacts,
which can be accessible to others in a public repository, rather than writing into
this cloud workspace. Review that delivery model before enabling it. It restores
prior delivery history and reports for independent evaluation. Artifacts expire
after 90 days, so longer interruptions require restoring retained history.
GitHub's scheduled execution can be delayed or disabled after inactivity.

## Limits and roadmap

Host/publisher labels are identity proxies, not proof of distinct people. Aliases
can evade matching; shared publishers can suppress different hosts. RSS title
patterns do not prove a show accepts pitches. Blocked feeds remain unverified.
A finite directory snapshot does not demonstrate sustained weekly lead supply.

Next improvements: verified host identities, stronger audience-fit evaluation,
source expansion when discovery stalls, and response/booking metrics after real
outreach. This routine does not send email. Reply rates are unmeasured.

See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute and [NOTICE.md](NOTICE.md) for
the original Gatsby repository history and license attribution.
