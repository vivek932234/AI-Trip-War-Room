# AI Trip War Room

> An AI-powered collaborative travel planning platform for trip
> creation, group coordination, role-based participation, expense
> tracking, and AI-assisted itinerary generation.

## Live links

-   **Application:** https://ai-trip-war-room.vercel.app/
-   **Backend:** https://ai-trip-war-room.onrender.com
-   **GitHub:** https://github.com/vivek932234/AI-Trip-War-Room

## Overview

AI Trip War Room is a full-stack web application that brings group
travel planning into one shared workspace. Users can register and log
in, create trips, invite participants through a link or code,
collaborate using Viewer and Planner roles, communicate through group
chat, track expenses, and generate AI-assisted travel plans. Generated
itineraries can be accessed through itinerary history/version
functionality.

## Problem statement

Group trips require participants to coordinate destinations, dates,
budgets, schedules, and decisions. When information is scattered across
chats and documents, it can become difficult to keep everyone aligned.
This application centralizes trip information and collaboration, with an
AI travel concierge to assist with itinerary generation.

## Objectives

1.  Centralize trip creation and management.
2.  Support invitation-based participation.
3.  Provide Viewer and Planner participation roles.
4.  Generate trip-specific itinerary suggestions with Google Gemini.
5.  Preserve itinerary history/version access.
6.  Support group communication and expense tracking.
7.  Deploy the frontend and backend to cloud hosting.

## Key features

-   User registration and login.
-   JWT-based authentication for protected operations.
-   Trip creation and retrieval.
-   Invitation link/code generation and joining flow.
-   Viewer and Planner roles.
-   AI travel-plan generation.
-   Itinerary history and version retrieval.
-   Group chat.
-   Expense tracking.
-   Gemini model fallback and retry handling.

## Technology stack

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Frontend                React 19, Vite          User interface and
                                                  client-side navigation

  Backend                 Python, FastAPI         REST APIs and
                                                  application logic

  Database                MongoDB Atlas           Persistent data storage

  Authentication          JWT                     Authenticated access

  AI                      Google Gemini API       AI travel-plan
                                                  generation

  Frontend hosting        Vercel                  React application
                                                  hosting

  Backend hosting         Render                  FastAPI service hosting
  -----------------------------------------------------------------------

Check `frontend/package.json` and `backend/requirements.txt` for exact
dependency versions in the current repository.

## System architecture

``` mermaid
flowchart TD
    U[Trip participant / browser] --> FE[React + Vite frontend on Vercel]
    FE -->|HTTPS requests with JWT| BE[FastAPI backend on Render]
    BE --> DB[(MongoDB Atlas)]
    BE --> AI[Google Gemini API]
    BE --> FE
```

The browser loads the React frontend from Vercel. The frontend calls the
FastAPI backend on Render. The backend validates requests and
permissions, reads/writes MongoDB data, and calls Gemini for
AI-generated itinerary content.

## Application workflow

1.  A user registers or logs in.
2.  The frontend uses authentication credentials for protected API
    requests.
3.  An authenticated user creates a trip.
4.  The trip owner invites participants using the available link/code
    flow.
5.  Participants join and access the trip according to their assigned
    role.
6.  Members use group collaboration features such as chat and expense
    tracking.
7.  A user requests an AI travel plan for a trip.
8.  The backend sends the request to Gemini, handles the response, and
    returns itinerary content.
9.  The generated plan can be accessed through itinerary history/version
    functionality.

## AI integration and model fallback

The backend uses the Google Gemini API through the Python client. Model
names are configured through environment variables.

The fallback sequence verified during deployment was:

1.  Primary: `gemini-3.8-flash`
2.  Fallback: `gemini-3.6-flash`
3.  Fallback: `gemini-3.5-flash-lite`

The service retries a model once after a short delay for HTTP
`503 UNAVAILABLE`, then switches to the next configured model. If a
model succeeds, its generated text is returned. If all configured models
fail, the backend returns a controlled temporary-unavailability error.

**Operational note:** Model identifiers, availability, and pricing can
change. Verify currently supported model IDs in Google's Gemini API
documentation before changing production settings. Multiple models do
not guarantee independent capacity or uninterrupted service.

## Security and access control

-   JWT authentication protects backend operations.
-   Secrets and environment-specific values are supplied through
    environment variables.
-   MongoDB access is controlled through Atlas database users and the IP
    access list.
-   Viewer and Planner are trip participation roles.
-   The backend must enforce identity, membership, and permissions;
    frontend-only restrictions are not sufficient.
-   Never commit `.env` files, API keys, database credentials, JWT
    secrets, or access tokens.

## Deployment

  -------------------------------------------------------------------------------------------------
  Component               Platform                URL
  ----------------------- ----------------------- -------------------------------------------------
  Frontend                Vercel                  https://ai-trip-war-room.vercel.app/

  Backend                 Render                  https://ai-trip-war-room.onrender.com

  Source code             GitHub                  https://github.com/vivek932234/AI-Trip-War-Room
  -------------------------------------------------------------------------------------------------

The frontend and backend are deployed separately. Render environment
variables hold backend configuration and secrets. A Render free instance
may spin down after inactivity, causing a cold-start delay.

## Repository structure

``` text
AI-Trip-War-Room/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   └── services/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
└── README.md
```

This is a high-level view; consult the current repository for the exact
tree.

## Local setup

### Prerequisites

-   Python 3.10 or a version supported by backend dependencies.
-   Node.js and npm compatible with frontend dependencies.
-   MongoDB Atlas (or another configured MongoDB deployment).
-   Google Gemini API key.
-   Git.

### 1. Clone the repository

``` bash
git clone https://github.com/vivek932234/AI-Trip-War-Room.git
cd AI-Trip-War-Room
```

### 2. Set up the backend

``` bash
cd backend
python -m venv venv
```

Activate on Windows PowerShell:

``` powershell
.\venv\Scripts\Activate.ps1
```

Activate on macOS/Linux:

``` bash
source venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Create a local `.env` file using the variable names required by
`backend/app/services/security.py`. Example values:

``` env
MONGODB_URL=your_mongodb_connection_string
JWT_SECRET_KEY=your_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACK_MODELS=gemini-3.6-flash,gemini-3.5-flash-lite
FRONTEND_URL=http://localhost:5173
```

Use your own credentials. Never commit this file.

Start FastAPI from the `backend` directory:

``` bash
python -m uvicorn app.main:app --reload
```

-   Swagger UI: http://127.0.0.1:8000/docs
-   OpenAPI schema: http://127.0.0.1:8000/openapi.json

### 3. Set up the frontend

In a second terminal:

``` bash
cd frontend
npm install
npm run dev
```

Vite prints the local development URL (commonly http://localhost:5173).
Check the frontend API client configuration for the exact environment
variable used for the backend base URL; Vite client-exposed variables
generally use the `VITE_` prefix.

## Backend configuration

  Variable                        Purpose
  ------------------------------- ------------------------------------
  `MONGODB_URL`                   MongoDB connection string
  `JWT_SECRET_KEY`                JWT signing secret
  `JWT_ALGORITHM`                 JWT signing algorithm
  `ACCESS_TOKEN_EXPIRE_MINUTES`   Token expiry setting
  `GEMINI_API_KEY`                Gemini API credential
  `GEMINI_MODEL`                  Primary Gemini model
  `GEMINI_FALLBACK_MODELS`        Comma-separated fallback model IDs
  `FRONTEND_URL`                  Frontend origin/application URL

Follow the current settings module if variable names or defaults differ.

## API overview

The following AI endpoints were visible in the project's FastAPI Swagger
documentation:

  ---------------------------------------------------------------------------------------------
  Method                  Endpoint                                      Purpose
  ----------------------- --------------------------------------------- -----------------------
  POST                    `/ai/travel-plan`                             Generate a travel plan

  POST                    `/ai/trips/{trip_id}/travel-plan`             Generate a
                                                                        trip-specific travel
                                                                        plan

  GET                     `/ai/trips/{trip_id}/itineraries`             Retrieve itinerary
                                                                        history

  GET                     `/ai/trips/{trip_id}/itineraries/{version}`   Retrieve a specific
                                                                        itinerary version

  POST                    `/ai/trips/{trip_id}/chat`                    Send a message to the
                                                                        AI

  GET                     `/ai/trips/{trip_id}/chat/history`            Retrieve AI chat
                                                                        history
  ---------------------------------------------------------------------------------------------

Other route groups cover authentication, trips, membership/invitations,
group chat, and expenses. Run the backend and inspect `/docs` for the
authoritative full endpoint list and request/response schemas.

## Testing and verification

The following workflows were exercised during development and
deployment:

-   Registration and login.
-   MongoDB Atlas connectivity.
-   Trip creation and retrieval.
-   Invitation and Viewer/Planner joining flow.
-   AI itinerary generation and itinerary history.
-   Group chat and expense-related functionality.
-   Frontend/backend production connectivity.
-   Gemini fallback behavior when the primary model returned 503.

A production log showed the primary model returning 503, a fallback
model being attempted, and a subsequent retry succeeding. The
trip-specific travel-plan endpoint returned HTTP `200 OK`.

Repeat these checks after changes to authentication, permissions,
database models, AI configuration, or deployment settings. This list
records manual verification and is not a claim of a complete automated
test suite.

## Challenges and resolutions

### MongoDB Atlas connectivity

Local startup initially encountered a MongoDB TLS/SSL handshake and
server-selection failure. The Atlas IP access list was checked and the
current public IP was added. A subsequent local startup logged a
successful MongoDB connection.

### Gemini service overload

Gemini returned `503 UNAVAILABLE` due to temporary model demand. The
backend was updated with retry handling and a configurable model
fallback sequence. Production logs later confirmed successful generation
using a fallback model.

### Cloud deployment configuration

The backend changes were committed and pushed to GitHub, and the
fallback-model environment variable was added in Render to trigger a new
deployment. Production logs confirmed the updated fallback behavior.

## Known operational considerations

-   AI generation depends on Gemini service availability, limits, and
    policies.
-   Model fallback improves resilience but cannot guarantee
    uninterrupted AI service.
-   Render free services can spin down after inactivity.
-   MongoDB Atlas requires valid credentials and network access-list
    configuration.
-   Keep all secrets out of Git.
-   Verify current Gemini model availability and pricing before changing
    model configuration.

## Future enhancements

-   Automated unit, integration, and end-to-end test coverage.
-   CI checks for linting, tests, and deployment.
-   Structured monitoring, metrics, and alerting.
-   Expanded itinerary editing, group voting, and collaboration.
-   PWA installation and offline-friendly read-only access (not claimed
    as completed).
-   Accessibility and broader cross-device usability testing.

## Project developer

**Vivek Sawwalakhe**

Developed as an internship project. Add mentor, institution, team, or
acknowledgement details if required for formal submission.

## License

No license is specified here. Add a `LICENSE` file and update this
section if the repository is intended for open-source distribution.
