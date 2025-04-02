FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# The API key should be provided at runtime
ENV OPENAI_API_KEY=""

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]