# Architecture

## Runtime

The current game is delivered as a static, single-page web application:

- `src/game/index.html` contains the HTML shell, styles, gameplay logic, and UI rendering.
- `src/assets/` contains local artwork and interface resources.
- `src/game/manifest.webmanifest` defines the installable PWA metadata.
- `src/game/service-worker.js` provides offline caching after an initial successful online load.
- `src/platform/` defines provider-neutral contracts for advertising and cloud saves.

This repository documents the implementation as it exists. It does not claim a component framework, build pipeline, backend, or native wrapper that is not present in the source bundle.

## Main Runtime Domains

1. **Business progression** — shop ownership, upgrades, income collection, and regional progression.
2. **Manager roster** — manager identity, rarity, progression, abilities, and team selection.
3. **Recruitment** — ordinary and advanced recruitment, pity counters, duplicate conversion, and rewards.
4. **Tasks and campaigns** — daily, weekly, monthly, achievement, and rotating campaign progress.
5. **Offline settlement** — elapsed-time calculation and capped offline reward collection.
6. **Persistence** — local save data and schema-compatible migration behavior.

## Save Compatibility

The current documented save schema is v6. Stable manager IDs are important because manager levels, experience, stars, breakthroughs, and shards are associated with those IDs. Changes to IDs or save fields must be accompanied by migration tests.
