# Worker Application for AI Interviewer

This is the worker application for the AI Interviewer project. It is designed to process background tasks asynchronously, specifically handling messages from the Azure Service Bus related to interview recordings and other tasks.

## Project Structure

```
worker
├── app
│   ├── __init__.py          # Initializes the worker application package
│   ├── main.py              # Entry point of the FastAPI worker application
│   ├── processor.py         # Logic for processing messages from Azure Service Bus
│   ├── servicebus_listener.py# Implements the Azure Service Bus listener
│   └── requirements.txt      # Lists dependencies required for the worker application
├── Dockerfile.worker         # Instructions to build a Docker image for the worker application
└── README.md                 # Documentation for the worker application
```

## Setup Instructions

1. **Clone the Repository**: 
   Clone the repository to your local machine.

2. **Navigate to the Worker Directory**: 
   Change into the `worker` directory.

3. **Install Dependencies**: 
   Use the following command to install the required dependencies:
   ```
   pip install -r app/requirements.txt
   ```

4. **Run the Application**: 
   Start the FastAPI worker application using:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

5. **Docker Setup**: 
   To build and run the Docker container, use the following commands:
   ```
   docker build -f Dockerfile.worker -t worker-app .
   docker run -p 8000:8000 worker-app
   ```

## Usage

The worker application listens for messages from the Azure Service Bus. When a new message is received, it processes the message and updates the database accordingly. 

## Development Notes

- Ensure that the Azure Service Bus connection string and other configurations are set in the environment variables or configuration files as needed.
- Follow the coding standards and modular design principles established in the backend application to maintain consistency across the project.

## Contributing

Contributions are welcome! Please follow the project's coding standards and guidelines when making changes.