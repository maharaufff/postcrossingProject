from db import db

users = [
    {"username": "maha123", "email": "maha@example.com", "country": "Pakistan"},
    {"username": "john_doe", "email": "john@example.com", "country": "USA"},
    {"username": "sara_smith", "email": "sara@example.com", "country": "UK"},
    {"username": "li_wei", "email": "li@example.com", "country": "China"}
]

postcards = [
    {"code": "PK-10001", "title": "Lahore Fort", "description": "Beautiful postcard from Pakistan"},
    {"code": "US-20002", "title": "Golden Gate Bridge", "description": "Famous bridge in San Francisco"},
    {"code": "UK-30003", "title": "Big Ben", "description": "Iconic London postcard"},
    {"code": "CN-40004", "title": "Great Wall", "description": "Historic wall of China"}
]


transactions = [
    {"sender": "maha123", "receiver": "john_doe", "postcard_code": "PK-10001", "status": "sent"},
    {"sender": "john_doe", "receiver": "sara_smith", "postcard_code": "US-20002", "status": "sent"},
    {"sender": "sara_smith", "receiver": "li_wei", "postcard_code": "UK-30003", "status": "sent"},
    {"sender": "li_wei", "receiver": "maha123", "postcard_code": "CN-40004", "status": "sent"}
]


db.users.insert_many(users)
db.postcards.insert_many(postcards)
db.transactions.insert_many(transactions)

print("✅ Mock data inserted successfully!")

