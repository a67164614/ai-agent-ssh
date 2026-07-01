# AI Ops Panel Scaffold Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a runnable MVP foundation for an AI-assisted SSH operations panel.

**Architecture:** Use a React/Vite frontend served separately in development and built into static assets for Docker. Use a FastAPI backend for auth, settings, server records, deployment plan validation, command safety checks, and future SSH/WebSocket orchestration. Keep the first version single-container friendly with SQLite storage and a clean upgrade path to PostgreSQL and a background queue.

**Tech Stack:** React, Vite, TypeScript, FastAPI, Pydantic, SQLAlchemy, SQLite, pytest, Docker Compose.

---

### Task 1: Backend Safety Domain

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/tests/test_command_safety.py`

**Steps:**
1. Write pytest coverage for dangerous command detection.
2. Run `python -m pytest backend/tests/test_command_safety.py -v` and confirm it fails because the module is missing.
3. Implement `is_dangerous_command`.
4. Re-run the test and confirm it passes.

### Task 2: Deployment Plan Validation

**Files:**
- Create: `backend/app/schemas/deployment.py`
- Create: `backend/tests/test_deployment_plan.py`

**Steps:**
1. Write pytest coverage for accepted deployment plans and rejected dangerous steps.
2. Run the targeted tests and confirm failure.
3. Implement Pydantic models and validation.
4. Re-run targeted tests and full backend tests.

### Task 3: FastAPI App Shell

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/routes.py`
- Create: `backend/app/core/config.py`
- Create: `backend/tests/test_api.py`

**Steps:**
1. Write API tests for `/api/health`, `/api/commands/check`, and `/api/deployments/validate-plan`.
2. Run the tests and confirm failure.
3. Implement the routes.
4. Re-run API tests.

### Task 4: Persistence Foundation

**Files:**
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/models.py`
- Create: `backend/app/db/init_db.py`

**Steps:**
1. Add SQLAlchemy models for users, servers, AI providers, and audit logs.
2. Initialize SQLite tables on startup.
3. Keep API endpoints minimal and avoid implementing real SSH execution in this scaffold.

### Task 5: Frontend Shell

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/styles.css`

**Steps:**
1. Create a TypeScript Vite app shell.
2. Add dashboard sections for servers, AI settings, deployment workflow, terminal placeholder, and audit history.
3. Add commands for type checking and build.

### Task 6: Docker And Documentation

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `README.md`
- Create: `docs/deployment.md`

**Steps:**
1. Build frontend assets in Docker.
2. Install backend dependencies and serve FastAPI on port 8080.
3. Document local development, Docker Compose deployment, environment variables, and first-run notes.
4. Run backend tests, frontend build, and Docker config validation.
5. Commit the scaffold.
