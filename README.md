# Business Empire: Text Tycoon

> A browser-based idle business game developed through a multi-model AI-assisted workflow, demonstrating requirement decomposition, AI output evaluation, integration, and iterative refinement.

**Personal Project | AI-Assisted Development | HTML5 / JavaScript**

## Project Overview

**Business Empire: Text Tycoon** is a browser-based idle business management game concept. The project began with a gameplay vision and requirements covering progression, visual direction, user interface, and game features. AI tools supported the process of turning that vision into a functional browser-based prototype.

This project demonstrates how multiple AI tools can be coordinated in a practical development workflow. Rather than claiming that every component was independently programmed, the focus is on requirement decomposition, evaluating AI-generated outputs, and integrating code and visual assets into one coherent project.

## My Role & Responsibilities

I was responsible for defining the project direction and coordinating the overall AI-assisted development process.

- Conceived and planned the browser-based idle business game.
- Defined the gameplay direction, visual style, user interface, and desired features.
- Decomposed overall project requirements into smaller tasks for AI-assisted production.
- Evaluated AI-generated code and visual assets against the intended design and functionality.
- Provided feedback and directed iterative improvements.
- Integrated generated code and visual assets into a unified project.

## Multi-Model AI Workflow

Different AI tools were used for different stages of development.

| AI Tool | Responsibilities |
|---|---|
| **Claude** | Generated the initial game source code based on the overall project requirements. |
| **ChatGPT** | Supported visual asset generation, subsequent code refinements, and iterative debugging. |
| **Google Gemini** | Supported visual asset generation and occasional prompt optimization. |

### Development Workflow

1. **Planning** — Defined the game concept, gameplay direction, visual style, interface, and desired features.
2. **Requirement Decomposition** — Divided broad project requirements into smaller, manageable tasks.
3. **AI-Assisted Generation** — Used different AI tools to generate initial code and visual assets.
4. **Output Evaluation** — Reviewed generated results against the intended requirements and identified issues.
5. **Iterative Refinement** — Provided targeted feedback and directed improvements.
6. **Integration** — Combined accepted code and visual assets into the browser-based game.
7. **Testing & Improvement** — Reviewed the integrated results, identified problems, and continued refining the project.

## Game Features

The prototype explores several idle business management systems:

- Idle business progression and shop upgrades
- Collectible managers and manager progression
- Recruitment and reward systems
- Offline income and time-based progression
- Tasks, events, and progression incentives
- Browser-based gameplay with Progressive Web App (PWA) support

Feature completeness varies across systems. Please refer to the source code and project documentation for implementation details.

## Technology & Tools

- **Programming:** HTML, CSS, JavaScript
- **Platform:** Browser-based H5 Game / Progressive Web App
- **AI Tools:** Claude, ChatGPT, Google Gemini
- **Supporting Materials:** Python and JavaScript-based QA and simulation scripts

My programming foundation includes Python fundamentals and basic NumPy. This project primarily demonstrates practical experience in coordinating AI-assisted development workflows rather than claiming advanced independent programming expertise.

## Repository Structure

```text
.
├── src/
│   ├── game/                 # Game source code, PWA files, and assets
│   └── platform/             # Platform integration contracts
├── scripts/
│   ├── qa/                   # QA and simulation scripts
│   └── regression/           # Regression checks
├── research/
│   ├── economy/              # Economy datasets and workbooks
│   ├── managers/             # Manager roster and balance datasets
│   └── metadata/             # Simulation metadata
└── docs/
    ├── ARCHITECTURE.md
    ├── GAME_SYSTEMS.md
    ├── ECONOMY_AND_BALANCING.md
    ├── AI_WORKFLOW.md
    ├── QA_AND_VALIDATION.md
    ├── PLATFORM_INTEGRATIONS.md
    └── ROADMAP.md
```

## Running Locally

This project is a static web application.

To run it locally, use Python's built-in HTTP server:

```bash
python -m http.server 8000 --directory src/game
```

Then open:

http://localhost:8000

Serving the game through localhost is recommended for testing browser features such as service-worker behavior.

## Project Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Gameplay Systems](docs/GAME_SYSTEMS.md)
- [Economy & Balancing](docs/ECONOMY_AND_BALANCING.md)
- [AI-Assisted Workflow](docs/AI_WORKFLOW.md)
- [QA & Validation](docs/QA_AND_VALIDATION.md)
- [Platform Integrations](docs/PLATFORM_INTEGRATIONS.md)
- [Roadmap & Known Limitations](docs/ROADMAP.md)

## Scope & Limitations

This repository contains a development prototype and supporting project materials, not a production release.

- The current game runtime is a browser-based HTML application.
- External advertising and cloud-save services are represented by integration contracts. Production SDKs and credentials are not included.
- Automated QA scripts and historical test reports are included, but the reports should not be interpreted as fresh validation of every file in this reorganized repository.
- Real-device visual QA, production platform integration, and release preparation remain separate tasks.

## What This Project Demonstrates

- Multi-model AI tool coordination
- Prompt engineering and prompt refinement
- Requirement decomposition
- Evaluation of AI-generated code and visual assets
- Integration of AI-generated outputs into a functional browser-based project
- Iterative testing, issue identification, and AI-assisted debugging

**The central objective of this project is to demonstrate how AI tools can be effectively coordinated as part of a structured development workflow — from defining requirements and guiding generation to evaluating outputs and integrating improvements into a functional application.**
