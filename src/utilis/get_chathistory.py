import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_chat_history(session_id):
    # Get the MongoDB URI from environment variable
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise ValueError("MONGODB_URI not found in environment variables.")

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    
    # Access the database and collection
    db = client["pigen"]
    collection = db["chatmessages"]

    results = collection.find(
        {"chatsessionId": session_id},
        {"_id": 0, "messageType": 1, "messageContent": 1}
    ).sort("sentAt", 1)

    # Convert the results to a list of dictionaries
    chat_history = list(results)

    # Optional: Close the connection (MongoClient uses lazy connection pooling so not strictly needed)
    client.close()
    return chat_history
