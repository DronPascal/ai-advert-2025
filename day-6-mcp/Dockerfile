FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx duckduckgo_search==6.1.7 \
    beautifulsoup4 lxml

COPY server.py /app/server.py

EXPOSE 8765

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]



