# Architecture and data model

~~~mermaid
flowchart LR
  A[MBTA official alerts API] --> C[Source adapter]
  B[CTA official alerts API] --> C
  C --> D[Normalize and validate]
  D --> E[Content hash and change detection]
  E --> F[(PostgreSQL)]
  E --> G[One alert per notice revision]
  F --> H[FastAPI]
  G --> H
  H --> I[React + Vite dashboard]
  J[APScheduler] --> C
~~~

~~~mermaid
erDiagram
  AGENCIES ||--o{ NOTICES : owns
  NOTICES ||--o{ NOTICE_REVISIONS : retains
  NOTICES ||--o{ ALERT_DELIVERIES : creates
  AGENCIES {
    int id PK
    string key UK
    string name
    string source_url
  }
  NOTICES {
    uuid id PK
    int agency_id FK
    string external_id
    json route_ids
    string content_hash
    int revision_number
    datetime last_confirmed_at
    boolean is_withdrawn
  }
  NOTICE_REVISIONS {
    int id PK
    uuid notice_id FK
    int revision_number
    json snapshot
    datetime observed_at
  }
  ALERT_DELIVERIES {
    int id PK
    uuid notice_id FK
    int revision_number
    string channel
    string recipient
    string status
  }
  COLLECTOR_RUNS {
    int id PK
    string source_key
    string state
    datetime started_at
    datetime finished_at
  }
~~~

The database migration creates a unique key for `(agency_id, external_id)` and a unique delivery key for `(notice_id, revision_number, channel, recipient)`. Those two constraints make source retries and alert retries safe to repeat.
