# QA & Validation

## Automated Regression

The original project bundle includes Node.js and Python checks covering:

- Source and asset integrity
- Six-region / 30-business catalogue structure
- Core gameplay logic
- UI resource references
- Map and navigation behavior
- Save migration and recurring task cycles
- Team and offline reward logic
- Manager traffic and campaign behavior
- Long-horizon manager reward simulation

## Running Checks

The original aggregate runner was located at `project_docs/qa/run_all_checks.sh` in the source bundle. Individual scripts are retained under `scripts/qa/` and `scripts/regression/`.

Because this portfolio reorganization changes file locations, some original scripts may contain historical relative paths. Run them from their expected project layout or update paths before treating the aggregate suite as reproducible in this reorganized repository.

## Validation Status at Source Bundle v1.36

The supplied QA report records all bundled automated checks as passing. It explicitly leaves real-browser and physical-device visual QA open. It also identifies production ad SDK, cloud-save configuration, and native packaging as incomplete.

Do not interpret the source-bundle QA report as a fresh test run against this reorganized GitHub package.
