# CLAUDE.md

# MapApp — Project Instructions

## Project Overview

MapApp is a location-based civic and community application.

The initial goal is to allow people to:

* View civic issues and requests on an interactive map.
* Create a request or complaint at a specific geographic location.
* View details of existing reports.
* Upvote reports.
* Comment on reports.
* Share reports.
* Eventually allow municipalities and organizations to participate.

The long-term vision is to expand MapApp into a location-based community platform where civic issues, activities, events, organizations, and local announcements coexist on the same map.

The project is currently a **demo/MVP**, not a production application.

## Development Philosophy

Priorities, in order:

1. Keep the architecture simple.
2. Build working vertical slices.
3. Avoid premature optimization.
4. Prefer established, boring technologies over unnecessary complexity.
5. Keep the application easy for another developer to understand.
6. Do not introduce infrastructure or dependencies unless they solve a current problem.

This is also a learning project. Explain important architectural decisions when they are not obvious.

## Incremental Development and Verification

Build this project in small, ordered steps. Each step must be verified as working before starting the next one.

A step is not finished until it has been *observed* working, not merely written:

* Start the relevant service and confirm it actually runs.
* Exercise the new behaviour end to end (an HTTP request, a page load, a query), not just the code path in isolation.
* Run the relevant tests and linters for that step.
* If a step cannot be verified, say so explicitly rather than moving on.

Do not stack several unverified steps and check them all at the end. When something breaks, the cause should be traceable to the one change that introduced it.

Report verification results honestly. If a check fails, was skipped, or was not possible in the current environment, state that plainly along with the actual output.

## Planned Technology Stack

### Backend

* Python
* Django
* Django REST Framework
* PostgreSQL
* PostGIS for geographic queries

### Frontend

* React
* Next.js
* TypeScript

The frontend should remain relatively simple because the primary developer has limited frontend experience.

### Infrastructure

* Docker
* Amazon S3 for user-uploaded images
* GitHub for source control
* GitHub Actions for CI/CD

Do not introduce AWS services unless they are actually needed.

## Architecture

Start with a simple architecture:

Browser
→ Next.js frontend
→ Django REST API
→ PostgreSQL/PostGIS

Images:

Browser
→ S3

The backend should remain a modular monolith.

Do NOT introduce microservices.

Do NOT introduce Kafka, RabbitMQ, GraphQL, Redis, or other infrastructure unless a concrete requirement appears.

## Initial MVP

The first version should focus on:

1. User authentication
2. Interactive map
3. Creating a report/request at a geographic location
4. Displaying reports on the map
5. Report detail page
6. Upvoting
7. Comments
8. Basic image upload
9. Basic report status

Do not implement Phase 2 activities yet unless explicitly requested.

Do not implement advertising or monetization.

## Geographic Data

Geographic information is a core part of the application.

Use PostgreSQL + PostGIS rather than storing latitude and longitude as unrelated numeric fields.

The design should allow future queries such as:

* reports within a radius
* reports inside a map bounding box
* nearby activities
* nearby organizations
* geographic aggregation

## API

Use REST APIs through Django REST Framework.

Keep API endpoints predictable and resource-oriented.

Prefer:

GET    /api/reports/
POST   /api/reports/
GET    /api/reports/{id}/
POST   /api/reports/{id}/upvote/
POST   /api/reports/{id}/comments/

over complicated endpoint structures.

## Code Quality

Use:

* Ruff for Python linting/formatting
* TypeScript on the frontend
* ESLint
* Prettier
* pytest/Django testing tools

Tests should focus especially on:

* business logic
* permissions
* geographic queries
* voting behavior
* report status transitions
* API behavior

Do not require exhaustive test coverage for the MVP.

We are not practicing strict TDD. Prefer implementing a feature first and adding meaningful tests around important behavior.

## Git

Use Git from the beginning.

Use feature branches for significant changes:

feature/map
feature/reports
feature/comments
feature/voting

Keep commits small and meaningful.

Do not make large unrelated changes in one commit.

Never commit:

* secrets
* API keys
* passwords
* .env files containing secrets
* AWS credentials

## Environment Configuration

Use environment variables for configuration and secrets.

Provide `.env.example`.

Never hard-code:

* database passwords
* API keys
* AWS credentials
* map provider credentials

## Docker

Use Docker for local development so the development environment is reproducible.

Local development should eventually be possible with a simple command such as:

docker compose up

## AI-Assisted Development

This project is being developed heavily with AI assistance.

Before making significant architectural changes:

1. Inspect the existing project.
2. Explain the proposed approach.
3. Identify important trade-offs.
4. Make the smallest reasonable change.
5. Run relevant tests/linting.
6. Summarize what changed.

Do not rewrite existing working code unnecessarily.

Do not add dependencies simply because they make implementation slightly easier.

## Important Rule

When requirements are ambiguous, prefer the simplest implementation that keeps the architecture extensible.

Do not build future features before they are needed.

The current goal is to get a small but working MapApp MVP running locally.

