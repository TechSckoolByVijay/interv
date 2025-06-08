from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from worker.app.worker import listen_to_service_bus
#from worker import listen_to_service_bus
import asyncio
from shared.logger import logger
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(listen_to_service_bus())

@app.get("/")
def read_root():
    return {"message": "Worker application is running and listening for messages."}