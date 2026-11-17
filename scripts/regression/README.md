# QA — current automated checks

Run all available checks from the bundle root:

```bash
bash project_docs/qa/run_all_checks.sh
```

Or run each check individually:

```bash
node project_docs/qa/source_integrity_test.js
node project_docs/qa/logic_regression.js
node project_docs/qa/ui_resources_smoke_test.js
node project_docs/qa/map_navigation_smoke_test.js
node project_docs/qa/platform_offline_smoke_test.js
node project_docs/qa/save_task_cycle_test.js
```

## What the checks cover
- Source HTML has one current entry; inline JS syntax is checked through Node; local asset URLs exist; save schema and current documentation set are present.
- Recruitment rules (10+1, normal fixed base probabilities/no soft increment/50th-pull hard pity, advanced +10 percentage points from pull 71 and hard pity at 80), manager progress, ads simulation and offline cap.
- Resource icon image references and navigation/map assets.
- Full-bleed map and floating dock CSS invariants.
- PWA manifest, orientation, service worker syntax, unique precache list and local asset existence.
- Synthetic save schema v1–v6 import paths, non-destructive rejection of malformed/unsupported import, UTC task cycle rollover, sign-in carry-over and duplicate claim protection.

These are static/isolated Node checks. They do not replace real browser, physical mobile device, actual historic player save, real advertisement SDK, cloud backend or native-app testing. Those remain listed in `project_docs/OPEN_ITEMS.md`.


## Offline settlement math (v1.14)
Run `node project_docs/qa/offline_settlement_math_test.js` from the bundle root. This is a pure math check only; it does not prove runtime integration or real ad SDK behavior.
