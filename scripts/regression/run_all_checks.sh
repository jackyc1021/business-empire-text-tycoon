#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
node project_docs/qa/source_integrity_test.js
node project_docs/qa/shop_catalog_six_region_test.js
node project_docs/qa/logic_regression.js
node project_docs/qa/ui_resources_smoke_test.js
node project_docs/qa/map_navigation_smoke_test.js
node project_docs/qa/platform_offline_smoke_test.js
node project_docs/qa/save_task_cycle_test.js
node project_docs/qa/team_offline_reward_test.js
node project_docs/qa/manager_traffic_campaign_test.js
python qa/v1_31_runtime_regression.py
SIM_TMP="$(mktemp)"
python qa/manager_60day_reward_gacha_sim_v1_31.py > "$SIM_TMP"
cmp "$SIM_TMP" project_docs/MANAGER_60DAY_SIMULATION_SUMMARY_v1_31.json
rm -f "$SIM_TMP"
printf '
ALL AUTOMATED CHECKS PASSED. Real browser/device QA remains OPEN.\n'
