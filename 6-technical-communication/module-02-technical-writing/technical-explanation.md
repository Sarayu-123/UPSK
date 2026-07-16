# API Migration Plan: REST to GraphQL

ShopStream is migrating its API infrastructure from REST to GraphQL to improve developer velocity and client-side performance. 

## Why We Are Migrating
We currently use a REST API with 47 endpoints. This design introduces several inefficiencies:
* **High Maintenance**: The Frontend (FE - user interface) team spends significant sprint capacity maintaining custom aggregation endpoints to stitch data together.
* **Redundant Endpoints**: The mobile team requires different data shapes than web, leading to a proliferation of purpose-built endpoints.
* **Versioning Issues**: The Software Development Kit (SDK - helper libraries) team struggles to maintain backward compatibility across endpoints.
* **High Latency**: The Site Reliability Engineering (SRE - operations) team reports that mobile apps make slow, sequential REST calls.
* **Alternative Considered**: We rejected Backend-for-Frontend (BFF - custom APIs per client) patterns due to deployment and monitoring complexity.

## Migration Scope & Next Steps
We are migrating to GraphQL—a query language allowing clients to request exactly the data they need. 
* **Timeline & Team**: Three engineers will work full-time on the migration for 8 weeks.
* **Onboarding**: Since two engineers are new to GraphQL, they will pair program and learn during the first two weeks.
* **Transition**: We will run REST and GraphQL simultaneously to ensure uninterrupted service.
* **Expected Outcome**: This will eliminate 15 aggregation endpoints and reduce frontend API calls by 40%.

## Risks
* **Query Performance & Caching**: The backend team will monitor query latency and implement complexity limits. We will adjust the timeline as needed during implementation.
