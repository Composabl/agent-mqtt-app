FROM python:3.10-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy the application files
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose MQTT port
EXPOSE 1883

# Command to run the server
CMD ["python", "agent_inference.py"]