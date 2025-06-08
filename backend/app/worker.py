import json
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus import ServiceBusReceiveMode
from shared.models import Interview, QuestionAnswer

# Handler stubs (implement these)
def extract_pdf_text(payload):
    print("PDF extraction handler called:", payload)

def extract_audio_text(payload):
    print("Audio extraction handler called:", payload)

def evaluate_answer(payload):
    print("Evaluate answer handler called:", payload)

# Action dispatcher
TASK_DISPATCHER = {
    "pdf_extraction": extract_pdf_text,
    "audio_extraction": extract_audio_text,
    "evaluate_answer": evaluate_answer,
}

SERVICE_BUS_CONNECTION_STR = "<your_connection_string>"
TOPIC_NAME = "<your_topic_name>"
SUBSCRIPTION_NAME = "<your_subscription_name>"

def handle_message(message_body):
    try:
        data = json.loads(message_body)
        action_type = data.get("action_type")
        handler = TASK_DISPATCHER.get(action_type)
        if handler:
            handler(data)
        else:
            print(f"No handler for action_type: {action_type}")
    except Exception as e:
        print(f"Error handling message: {e}")

def listen_to_service_bus():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=SERVICE_BUS_CONNECTION_STR)
    with servicebus_client:
        receiver = servicebus_client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME,
            receive_mode=ServiceBusReceiveMode.RECEIVE_AND_DELETE
        )
        with receiver:
            print("Listening for messages...")
            for msg in receiver:
                handle_message(str(msg))
                # If you want to stop after one message, break here

if __name__ == "__main__":
    listen_to_service_bus()