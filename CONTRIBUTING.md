# Contributing

Issues and pull requests are welcome. Include the problem, expected behavior,
and a reproducible example. Use synthetic identities in examples and tests.
Do not commit prospect reports, delivery history, cached feeds, or credentials.

Use Python 3.12+ and run `python -m unittest -q` before submitting changes.
`python dry_run.py` is an optional live-network check; its generated evidence
is ignored by Git. Describe source failures and distinguish live results from
simulated scheduling. Improvements to identity matching, ICP precision, and
independent evals are especially useful.

Contributions are licensed under the project's MIT license.
