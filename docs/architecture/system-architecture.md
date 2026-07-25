# System architecture

```mermaid
flowchart TB
    BROWSER["Browser"]
    UI["React operator application"]
    LAB["AI Assessment Lab"]
    API["FastAPI API"]
    AUTH["Authentication and RBAC"]
    GOV["Governance services"]
    REPO["SQLAlchemy repositories"]
    DB["PostgreSQL"]
    ADAPTER["Sandbox financial adapter"]
    REDIS["Redis (provisioned)"]
    OPA["OPA (provisioned)"]

    BROWSER --> UI
    UI --> API
    UI --> LAB
    API --> AUTH
    AUTH --> GOV
    GOV --> REPO
    REPO --> DB
    GOV --> ADAPTER
    API -. no current runtime dependency .-> REDIS
    API -. no current runtime dependency .-> OPA
```

The operational control path is React → FastAPI → service → repository → PostgreSQL. The sandbox
adapter is reachable only through the financial-action service after status, policy, and budget
checks. The Assessment Lab runs deterministic analysis in the browser and does not write
operational financial records.

Docker Compose starts the frontend, backend, PostgreSQL, Redis, and OPA. The latter two are
provisioned extension points and are deliberately not shown as active enforcement dependencies.
