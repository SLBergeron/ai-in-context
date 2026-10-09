# AI in Context

AI in Context is a free live session I run every Thursday, 1 to 2 PM ET. Each week we pick one idea about working with AI agents and do it live, on a real task. The recordings go up on YouTube.

This repo holds what gets built in the sessions. One folder per episode. Each folder has its own README, code and tests, so you can watch the replay and run the same thing yourself.

## Episodes

| Ep | Date | Topic | Replay | Code |
|---:|---|---|---|---|
| 01 | Oct 8, 2026 | Delegating to agents | [Watch](https://youtu.be/G45VTbDvHFc) | [ep01-delegating-to-agents](ep01-delegating-to-agents/) |
| 02 | Oct 15, 2026 | Managing agent workflows | Live on Oct 15. [Register](https://lemonbrand.io/next/gh-repo) | After the session |

## Join the next one

- Register for the next session: https://lemonbrand.io/next/gh-repo
- All sessions and replays: https://lemonbrand.io/live

## Running the code

Every episode folder is self-contained. Go into the folder and follow its README.

```sh
git clone https://github.com/SLBergeron/gatsby-themes.git
cd gatsby-themes/ep01-delegating-to-agents
python -m unittest -q
```

Ep 01 needs Python 3.12 or newer and nothing else. No packages to install, no API keys. The tests run on GitHub Actions on every push ([.github/workflows/tests.yml](.github/workflows/tests.yml)).

## Where this repo came from

In Ep 01 I needed a repo to hand to the agent, so I grabbed an old one:

> So I'm just going to use, I don't know, Gatsby themes, which I haven't touched in like six years.

It started as a fork of Rocketseat's Gatsby themes. The agent cleared it out during the session. None of that code is left in the current files. It is still in the git history, under its original MIT license.

## Contributing

Issues and pull requests are welcome. Say which episode folder it's about. Use made-up names and emails in tests and examples. Don't commit prospect reports, delivery history, cached feeds or credentials (the `.gitignore` already blocks the usual folders).

## License

[MIT](LICENSE).
