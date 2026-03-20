# Event-Driven Microservices System

A simple e-commerce backend built with FastAPI, RabbitMQ, and PostgreSQL.

## Services
1. **Order Service**: Manages orders, saves them to DB, and triggers payment.
2. **Payment Service**: Processes payments asynchronously.
3. **Notification Service**: Sends final confirmations to users.

## How to Run
1. Open terminal in the project root.
2. Run command: `docker compose up --build -d`
3. Access API Documentation: `http://localhost:8000/docs`
4. View logs: `docker compose logs -f`