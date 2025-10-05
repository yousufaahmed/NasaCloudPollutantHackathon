FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8000"]
