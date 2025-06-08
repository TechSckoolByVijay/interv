# AI Interviewer API

This is a FastAPI application for the AI Interviewer project. It includes features for user authentication and interview management.

## Setup

1. Create a `.env` file with your database credentials.
2. Build and run the application using Docker:
   ```
   docker-compose up --build
   ```

## API Endpoints

- `POST /signup`: Create a new user.
- `POST /login`: Authenticate a user.
- `POST /interview`: Create a new interview.