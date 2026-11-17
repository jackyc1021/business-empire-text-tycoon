# Economy & Balancing

## Why Simulation Exists

Incremental games are highly sensitive to compounding growth. A progression curve that feels reasonable during the first few upgrades can become unstable over weeks of play. This project uses repeatable simulations to inspect:

- Shop income and upgrade-cost curves
- Long-horizon player progression
- Offline reward contribution
- Manager level and star growth
- Reward material supply and demand
- Diminishing returns and team-wide bonus stacking
- Recruitment outcomes and duplicate rewards

## Research Assets

The `research/` directory contains historical CSV outputs, simulation metadata, and manager/economy workbooks. Python scripts in `scripts/qa/` reproduce selected analyses.

## Interpretation Rules

- A simulation result is evidence for a design decision, not automatic approval to ship a parameter.
- Candidate values must remain distinguishable from confirmed runtime values.
- Any balance change should identify its assumptions, sample size, time horizon, and expected player impact.
- Changes to reward supply should be checked against the full progression loop, not one isolated subsystem.

## Current Design Constraints

- Offline earnings are capped at eight hours in the current design baseline.
- Rewarded-ad boosts are designed as optional incentives rather than mandatory progression gates.
- Manager bonuses are separated by responsibility to reduce double-counting.
- Customer traffic increases potential order demand; shop capacity constrains fulfilled orders.
- Income bonuses affect completed-order value rather than multiplying order quantity a second time.
