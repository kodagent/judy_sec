# Pull the base image
FROM python:3.9

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install necessary system dependencies
RUN apt-get update -y && \
    apt-get install -y openjdk-17-jdk poppler-utils tesseract-ocr

# Clean up APT when done
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /code

# Copy project
COPY . /code/

# Install Python dependencies
RUN pip install -r requirements.txt

# # Collect static files
# RUN python manage.py collectstatic --noinput

# # Install Daphne
# RUN pip install daphne

# Run the application
CMD ["daphne", "chatbackend.asgi:application", "--port", "$PORT", "--bind", "127.0.0.1"]
# CMD daphne chatbackend.asgi:application --port $PORT --bind 0.0.0.0
