# Podcast ICP for Lemonbrand

The customer is a small-business owner or operations leader who can buy practical
AI implementation. The outreach prospect is the host of a podcast those customers
listen to. These are different roles.

Primary targets are interview-led shows for **accounting/tax firm owners and
independent insurance agency owners**. These sectors are explicitly named on
[Lemonbrand's website](https://lemonbrand.io), checked October 8, 2026.
Secondary targets are shows for small-business owners about operations,
productivity, workflow automation, and practical AI adoption.

The relevant conversation is: identify repetitive work, build agents staff can
review, maintain them, and measure time saved. Pitch angles can come from inbox
audits, staff oversight, and the cost of maintaining AI workflows. Do not invent
customer results or claim experience not supplied by the owner.

Prioritize shows with a recent episode within 120 days, evidence of guest
interviews, a named host or publisher, and an official contact route. Title patterns
are clues; confirm actual guest interviews before pitching. Directory search is
US by default; English language and audience geography need manual verification.
Audience size and acceptance of guest pitches are unknown unless sourced.

Exclude consumer personal finance, entertainment, pure AI news, and developer
tutorials without evidence of a business-owner audience. Missing feed access or
ambiguous audience information puts a candidate in review, not a qualified lead.

Current keyword scoring is a discovery heuristic. A matching term does not prove
ICP fit. Manually review the first 20 candidates using the criteria above before
treating them as outreach-ready. Record confirmed fit and reasons to refine the
search terms. The novelty demo eval below does not measure ICP precision.

## Demo eval: are we finding new prospects?

Each report is independently compared with all earlier delivered reports.
Default weekly success requires **at least five new host/publisher identities,
zero repeated prospects, and zero missing contact identities**. Five is an initial
demo target, configurable in `profile.json`, rather than a promised yield.

Matching uses show ID, normalized host/publisher name, and public email when
available. A new podcast belonging to a previously delivered publisher counts
as a repeat and is suppressed. Empty batches fail the new-prospect goal even
when they contain no repeats. Every run records counts, novelty rate, repeat
evidence, and eval pass/fail in JSON and Markdown. Discovery failures remain
operational failures; an eval failure is visible but does not cause an endless
retry that sends the same delivered prospects again.

Names and email addresses are identity proxies. This does **not** prove every
row is a distinct human: aliases or co-host changes can evade matching, and a
shared publisher can cover multiple hosts. Confirm individual identities before
outreach. Retain both `reports/` and `state/` for local weekly operation. Losing
both removes the reference history and invalidates cross-week novelty claims.

Run the independent eval with:

```sh
python evaluate.py reports/<timestamp>.json --history reports
```

Exit 0 means pass and exit 1 means the novelty target was missed. A first run is
a baseline against empty history; repeat-run tests are needed to demonstrate
suppression. Same-day reruns test deduplication, not sustained weekly yield.

## Reproducible dry-run baseline

Run `python dry_run.py`. It uses a separate `dry-runs/<timestamp>/` directory,
records one live public source snapshot (including failures), and replays it for
simulated weekly runs. The scheduler clock is simulated; report timestamps retain
actual execution times. Discovery calls are routed to isolated state instead of
production paths. It checks that the live report and state files remain unchanged.

The October 8, 2026 baseline delivered 20 new identities, then 17 more, then zero
as the same source pool was exhausted. No repeats were delivered. A second tick
within the same week was skipped. The exhausted batch correctly failed the
five-new-prospect target. An injected new show from an existing publisher also
failed the novelty eval. Six mechanics checks passed; the existing 10 tests passed.

Use `dry-runs/<timestamp>/SUMMARY.md`, `result.json`, the source manifest, and
individual CSV/JSON reports as review evidence. This benchmark proves repeat
suppression on a finite captured pool, not sustainable weekly yield, distinct
human identities, ICP precision, email replies, or an always-on scheduler.
Keep the mechanics pass/fail separate from each run's prospecting eval: a
correctly detected empty batch is a mechanics pass and a prospecting failure.

## Later eval: replies

After real outreach begins, record a stable prospect identity, message ID, send
date, delivery/bounce status, and reply date/type. Measure human reply rate and
positive reply/booking rate among delivered emails after a defined observation
window, such as 14 days. Exclude auto-replies and distinguish declines from
interest. Those outcomes are not available in this demo and are recorded as
unmeasured rather than zero. Do not send emails as part of this discovery job.
