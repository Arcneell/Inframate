# NetOps Flow

A self-hosted NetDevOps platform featuring an IPAM and a Script Runner.

## Architecture
- **Backend**: FastAPI (Python 3.11)
- **Worker**: Celery + Redis
- **Database**: PostgreSQL
- **Frontend**: Vue.js 3 + TailwindCSS + PrimeVue

## Getting Started

1. Ensure Docker and Docker Compose are installed.
2. Run the stack:
   ```bash
   docker-compose up --build
   ```

3. Access the services:
   - **Frontend**: http://localhost:3000
   - **API Docs**: http://localhost:8000/docs

## Features
- **IPAM**: Manage subnets (CIDR validation) and allocate IP addresses.
- **Script Runner**: Upload `.py` or `.sh` scripts and execute them on the server. Logs (stdout/stderr) are captured and displayed in the UI.

## Default Credentials
- **DB**: netops / netopspassword
