FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/backend

COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY --from=frontend-build /app/frontend/dist frontend/dist
COPY deploy/startup.sh deploy/startup.sh
RUN chmod +x deploy/startup.sh

EXPOSE 8000
CMD ["/app/deploy/startup.sh"]
