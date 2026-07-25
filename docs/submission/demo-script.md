# NorseAI judge demo

Target duration: 4–5 minutes.

## 1. Frame the problem — 20 seconds

“Autonomous financial agents can act faster than a human approval process. NorseAI makes policy,
budget, fleet status, execution, and evidence one mandatory server-side workflow.”

## 2. Establish the control plane — 30 seconds

Sign in and open **Overview**. Point out live API health, enabled agents and fleets, budget
utilization, emergency state, recent governed actions, and audit events.

## 3. Show the governed agent — 45 seconds

Open **Agents**, **Fleets**, and **Policies**. Explain that the agent belongs to an
organization-owned fleet and receives deterministic policy assignments. Emphasize default denial
and deny precedence at equal priority.

## 4. Show budget enforcement — 40 seconds

Open **Budgets** and show transaction, daily, or monthly limits at agent, fleet, and organization
scope. Explain that all required scopes reserve budget before execution.

## 5. Execute and trace a decision — 55 seconds

Submit a sandbox financial action through `POST /api/v1/financial-actions`. Return to **Overview**
to show settlement. Open **Audit Center**, locate the event, and point out actor, request,
correlation, policy, spend, and execution evidence. Export CSV or JSONL.

## 6. Demonstrate emergency control — 35 seconds

Open **Emergency** and stop the fleet. Explain that subsequent actions are rejected before adapter
invocation. Restore the fleet only if the remaining demo requires it.

## 7. Show AI governance breadth — 60 seconds

Open **AI Assessment Lab** and run the one-click Healthcare Diagnostic AI assessment. Show risk,
compliance, findings, remediation, and the executive PDF/JSON/CSV exports. Clarify that this
deterministic browser workspace is separate from financial execution.

## Closing — 15 seconds

“NorseAI is both a live financial-agent control plane and an evidence-ready AI governance
workspace: authorize, constrain, stop, and prove every decision.”

## Recovery

If the backend is unavailable, use the Assessment Lab while the operator UI displays an explicit
offline state. Do not describe Redis, OPA, or external payments as active integrations.
