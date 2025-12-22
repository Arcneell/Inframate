FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
# nmap: Network scanning
# wget, gnupg: For installing PowerShell
# libicu72: Required dependency for PowerShell on Bookworm (explicitly ensuring it's there)
RUN apt-get update && apt-get install -y libpq-dev gcc nmap wget gnupg software-properties-common && rm -rf /var/lib/apt/lists/*

# Install PowerShell for Debian 12 (Bookworm)
RUN wget -q "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" && \
    dpkg -i packages-microsoft-prod.deb && \
    rm packages-microsoft-prod.deb && \
    apt-get update && \
    apt-get install -y powershell

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]