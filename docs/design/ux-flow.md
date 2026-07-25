# UX flow

```mermaid
flowchart LR
    LOGIN["Sign in"] --> OVERVIEW["Operator Overview"]
    OVERVIEW --> AGENT["Register agent"]
    AGENT --> FLEET["Assign fleet and organization"]
    FLEET --> POLICY["Create and assign policy"]
    POLICY --> BUDGET["Configure hierarchical budgets"]
    BUDGET --> ACTION["Submit governed financial action"]
    ACTION --> AUDIT["Review and export audit evidence"]
    OVERVIEW --> STOP["Emergency stop"]
    OVERVIEW --> LAB["AI Assessment Lab"]
```

The platform opens on the authenticated Overview. Governance setup proceeds from scope to policy
to budget. Execution results return to the dashboard and Audit Center. Emergency control remains a
separate, high-salience path. The Assessment Lab is a secondary workflow for AI risk evaluation.
