FROM python:3.11-slim

# Set working directory
WORKDIR /workspace

# Install system utilities
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose standard Cloud Run port
EXPOSE 8080

# Run Streamlit with Cloud Run compatible parameters
ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8080", "--server.address=0.0.0.0"]
