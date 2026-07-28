# NorseAI judge demo

Target duration: 4–5 minutes.

## 1. Frame the problem — 20 seconds

“Autonomous financial agents can act faster than a human approval process. NorseAI makes policy,
budget, fleet status, execution, and evidence one mandatory server-side workflow.”

## 2. Establish the control plane — 30 seconds

Sign in and open **Overview**. Point out live API health, enabled agents and fleets, budget
utilization, emergency state, recent governed actions, and audit events.

## 3. Create the governed hierarchy — 55 seconds

Open **Organizations** and create the demonstration organization. Open **Fleets**, create its
fleet, then open **Agents** and create an enabled financial agent in that fleet.

Open **Policies**, create an allow policy for the demonstration action, and assign it to the agent.
Emphasize default denial and deny precedence at equal priority.

## 4. Configure budget enforcement — 40 seconds

Open **Budgets** and configure transaction, daily, and monthly limits at agent, fleet, and
organization scope. Explain that all required scopes reserve budget before execution.

## 5. Execute, approve, and reverse — 60 seconds

Open **Financial Actions**, select the organization, fleet, and agent, enter a payment, and select
**Submit governed action**. Show the approved decision, policy, adapter, and audit references.
Reverse the settled transaction from the same page and show the reversed status.

## 6. Demonstrate denial and emergency control — 45 seconds

Open **Emergency** and stop the fleet. Explain that subsequent actions are rejected before adapter
invocation. Return to **Financial Actions**, submit another request, and show its denied decision.
Open **Audit Center**, locate the approval, reversal, emergency stop, and denial events, and point
out actor, request, correlation, policy, spend, and execution evidence. Export CSV or JSONL.

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
