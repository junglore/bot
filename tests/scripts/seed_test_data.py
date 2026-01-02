"""
Seed test user and a sample expedition package into the `jungledb` MongoDB database.

Usage:
  pip install pymongo python-dotenv
  python scripts/seed_test_data.py

This script is idempotent: it will not insert duplicate users/packages if they already exist.
"""

import os
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise SystemExit("MONGODB_URI not set. Please add it to your .env or environment variables.")

client = MongoClient(MONGODB_URI)
db = client["jungledb"]

# --- Seed a test user ---
USER_EMAIL = "test+seed@junglore.local"
user = db.users.find_one({"email": USER_EMAIL})
if user:
    print(f"Found existing user: {user.get('_id')}")
    user_id = str(user.get('_id'))
else:
    user_doc = {
        "name": "Seed Test User",
        "email": USER_EMAIL,
        "created_at": datetime.utcnow(),
    }
    res = db.users.insert_one(user_doc)
    user_id = str(res.inserted_id)
    print(f"Inserted test user: {user_id}")

# --- Seed a sample expedition package (Tadoba) ---
PACKAGE_TITLE = "Tadoba Expedition - Test Seed"
pkg = db.packages.find_one({"title": PACKAGE_TITLE})
if pkg:
    print(f"Found existing package: {pkg.get('_id')}")
    pkg_id = str(pkg.get('_id'))
else:
    package_doc = {
        "title": PACKAGE_TITLE,
        "description": "A sample 3-day Tadoba expedition for testing. Includes jeep safaris, guidance, and meals.",
        "region": "Tadoba",
        "heading": "Tadoba National Park",
        "duration": "3 days",
        "type": "expedition",
        "price": 45000,
        "currency": "INR",
        "features": {"vehicle": "jeep", "meals": "included", "guides": "experienced naturalists"},
        "status": True,
        "image": "https://junglore.com/images/tadoba.jpg",
        "additional_images": [],
        "date": []
    }
    res = db.packages.insert_one(package_doc)
    pkg_id = str(res.inserted_id)
    print(f"Inserted expedition package: {pkg_id}")

print("\n--- Quick test commands ---")
print("1) Create a session (replace <USER_ID> with the shown user id):")
print(f"   curl -X POST http://localhost:8000/sessions/ -H \"Content-Type: application/json\" -d '{{\"user_id\": \"{user_id}\", \"title\": \"Seed Test Session\"}}'\n")
print("2) Ask about expeditions (replace <SESSION_ID> with the returned session_id):")
print(f"   curl -X POST http://localhost:8000/sessions/<SESSION_ID>/message -H \"Content-Type: application/json\" -d '{{\"user_id\": \"{user_id}\", \"message\": \"Do you plan jungle safari expedition?\"}}'")
print("\nIf you want the script to also create a session, run it and I can add that step upon request.")
