FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 5000
EXPOSE 5000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]

# build with
# docker build -t bainrecs-backend:latest .
#
# Run it with .env file
# docker run -d -p 5000:5000 -v "$(pwd)/.env:/app/.env" bainrecs-backend:latest