# Business Empire: Text Tycoon

> An anime-inspired idle business management game prototype exploring incremental progression, manager collection, long-horizon economy design, and AI-assisted production workflows.

<p align="center">
  <strong>Portfolio Project · H5 / PWA · JavaScript · Economy Simulation · AI-Assisted Art Pipeline</strong>
</p>

## Project Overview

**Business Empire: Text Tycoon** is a browser-based management game prototype. Players start with a small street-side business, reinvest operating income, unlock larger commercial ventures, and build a team of collectible managers whose abilities influence the business.

This repository is organized as a public-facing engineering portfolio: the runnable prototype, platform integration contracts, art assets, automated regression checks, and selected economy research are separated into clear areas.

## Highlights

- **Idle + active management loop** — collect operating income, reinvest in shop upgrades, and expand through a multi-region business catalogue.
- **Manager collection and team building** — an 18-manager roster across five rarity tiers, with levels, stars, abilities, and a six-member active team.
- **Long-horizon economy work** — Python simulations and CSV outputs used to inspect progression curves, reward pacing, offline settlement, and diminishing returns.
- **PWA support** — landscape-oriented standalone web app with a service worker and local asset caching.
- **Provider-neutral integration design** — ad and cloud-save contracts are separated from vendor-specific SDKs.
- **AI-assisted creative workflow** — character and UI asset production is treated as a repeatable pipeline with explicit mapping and asset validation.

## Current Build

| Item | Value |
|---|---|
| Game version | 2.19.1 |
| Save schema | v6 |
| Source bundle | v1.36 |
| Runtime entry | [`src/game/index.html`](src/game/index.html) |
| Platform | H5 / Progressive Web App |
| Primary implementation | HTML, CSS, JavaScript |
| Simulation / QA | Python, Node.js |

## Run Locally

The game is a static web application. For the best PWA behavior, serve it from `localhost` rather than opening the HTML file directly.

```bash
python -m http.server 8000 --directory src/game
```

Then open:

- http://localhost:8000

The game references artwork under `src/game/assets`. If you run the page from a different web root, preserve the relative asset layout or adjust the asset base paths accordingly.

## Repository Layout

```text
.
├── src/
│   ├── game/                 # Runtime entry, manifest, service worker, and assets
│   └── platform/             # Provider-neutral integration contracts
├── scripts/
│   ├── qa/                   # Economy and long-horizon simulation scripts
│   └── regression/           # Runtime and integration regression checks
├── research/
│   ├── economy/              # Economy simulation datasets and workbooks
│   ├── managers/             # Manager balance and roster datasets
│   └── metadata/             # Machine-readable simulation metadata
└── docs/
    ├── ARCHITECTURE.md
    ├── GAME_SYSTEMS.md
    ├── ECONOMY_AND_BALANCING.md
    ├── AI_WORKFLOW.md
    ├── QA_AND_VALIDATION.md
    ├── PLATFORM_INTEGRATIONS.md
    └── ROADMAP.md
```

## Engineering Notes

- The current runtime is a single-page HTML application with embedded JavaScript and CSS. This is intentionally documented as the current architecture rather than presented as a modular framework application.
- Automated checks cover source integrity, catalogue structure, core logic, resources, map/navigation, save/task cycles, team/offline rewards, and manager campaign logic.
- Passing automated checks does **not** imply real-device visual acceptance. Browser and physical-device QA remain separate release gates.
- Real advertising SDKs, cloud-save credentials/backends, and native store packaging are not configured in this prototype.

## AI as a Production Tool

AI was used as part of an iterative production workflow across concept development, visual asset generation, code assistance, documentation, and economy-analysis support. The project emphasizes human review and integration rather than treating generated output as automatically production-ready.

See [AI Workflow](docs/AI_WORKFLOW.md) for the workflow, quality controls, and portfolio framing.

## Project Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Gameplay Systems](docs/GAME_SYSTEMS.md)
- [Economy & Balancing](docs/ECONOMY_AND_BALANCING.md)
- [AI-Assisted Workflow](docs/AI_WORKFLOW.md)
- [QA & Validation](docs/QA_AND_VALIDATION.md)
- [Platform Integrations](docs/PLATFORM_INTEGRATIONS.md)
- [Roadmap & Known Limitations](docs/ROADMAP.md)

## Portfolio Disclaimer

This is a development prototype and portfolio demonstration, not a production release. Some catalogue entries and economy parameters are design candidates rather than shipped runtime content. Platform integrations that require external credentials or SDKs are represented by contracts only.
