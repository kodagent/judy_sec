# Use the official Python image as the base
FROM python:3.9

# Install system dependencies
RUN apt-get update -y && \
    apt-get install -y openjdk-17-jdk poppler-utils tesseract-ocr wget gnupg2 google-chrome-stable nodejs && \
    curl -sL https://deb.nodesource.com/setup_21.x | bash - && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set the working directory
WORKDIR /workspace

# Copy the project files to the container
COPY . /workspace/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
RUN npm i -D playwright && npx playwright install
