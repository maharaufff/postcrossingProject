from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from db import db
import random
from datetime import datetime, timedelta
from bson import ObjectId
import threading
import time

app = Flask(__name__)
CORS(app)


# ---------------- BACKGROUND AUTO DELIVERY ---------------- #

def simulate_delivery(postcard_id, delay_seconds=120):
    """
    Automatically marks a postcard as received after a delay.
    Default delay = 2 minutes (120 seconds)
    """
    print(f"🚚 Delivery simulation started for {postcard_id}... will deliver in {delay_seconds}s")
    time.sleep(delay_seconds)

    postcard = db.postcards.find_one({"postcard_id": postcard_id})
    if not postcard or postcard["status"] != "traveling":
        return  # Skip if already delivered or not traveling

    receiver = postcard["receiver_id"]

    db.postcards.update_one(
        {"postcard_id": postcard_id},
        {"$set": {"status": "received", "received_date": datetime.utcnow()}}
    )
    db.transactions.update_one(
        {"postcard_id": postcard_id},
        {"$set": {"status": "received"}}
    )
    db.users.update_one(
        {"username": receiver},
        {"$inc": {"received_count": 1}, "$push": {"postcards_received": postcard_id}}
    )

    print(f"🎉 Auto-delivery complete: postcard {postcard_id} received by {receiver}!")


# ---------------- USER ROUTES ---------------- #

@app.route("/register", methods=["POST"])
def register_user():
    name = request.form.get("name")
    email = request.form.get("email")
    country = request.form.get("country")
    address = request.form.get("address")

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    if db.users.find_one({"username": name}):
        return jsonify({"error": f"User '{name}' already exists"}), 409

    user = {
        "user_id": str(ObjectId()),
        "username": name,
        "email": email,
        "address": address or "N/A",
        "country": country or "N/A",
        "registered_date": datetime.utcnow(),
        "sent_count": 0,
        "received_count": 0,
        "postcards_sent": [],
        "postcards_received": []
    }

    db.users.insert_one(user)
    return jsonify({"message": f"✅ User {name} registered successfully!"}), 201


@app.route('/users', methods=['GET'])
def get_users():
    try:
        users_cursor = db.users.find({}, {'_id': 0, 'username': 1, 'email': 1, 'country': 1})
        users = list(users_cursor)
        return jsonify(users), 200
    except Exception as e:
        print("Error fetching users:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- POSTCARD ROUTES ---------------- #

@app.route("/add_postcard", methods=["POST"])
def add_postcard():
    try:
        code = request.form.get("code")
        message = request.form.get("message")
        image_url = request.form.get("image_url")
        sender = request.form.get("sender")

        if not code or not sender:
            return jsonify({"error": "Postcard code and sender are required"}), 400

        if db.postcards.find_one({"postcard_id": code.strip()}):
            return jsonify({"error": f"Postcard '{code}' already exists"}), 409

        postcard = {
            "postcard_id": code.strip(),
            "sender_id": sender.strip(),
            "receiver_id": None,
            "message": message.strip() if message else "",
            "image_url": image_url.strip() if image_url else "",
            "sent_date": None,
            "received_date": None,
            "status": "pending"
        }

        db.postcards.insert_one(postcard)
        return jsonify({"message": f"✅ Postcard '{code}' added successfully!"}), 201

    except Exception as e:
        print("Error adding postcard:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- TRANSACTION ROUTES ---------------- #

@app.route("/send_postcard", methods=["POST"])
def send_postcard():
    # ✅ Accept both JSON and FormData
    data = request.get_json(silent=True) or request.form

    sender = data.get("sender") or data.get("sender_id")
    receiver = data.get("receiver") or data.get("receiver_id")
    postcard_id = data.get("postcard_id")
    message = data.get("message", "")
    image_url = data.get("image_url", "")

    if not sender or not receiver or not postcard_id:
        return jsonify({"error": "sender, receiver, and postcard_id are required"}), 400

    sender_user = db.users.find_one({"username": sender})
    receiver_user = db.users.find_one({"username": receiver})
    postcard = db.postcards.find_one({"postcard_id": postcard_id})

    if not sender_user:
        return jsonify({"error": f"Sender '{sender}' not found"}), 404
    if not receiver_user:
        return jsonify({"error": f"Receiver '{receiver}' not found"}), 404
    if not postcard:
        return jsonify({"error": f"Postcard '{postcard_id}' not found"}), 404

    # 📨 Mark postcard as sent (traveling)
    db.postcards.update_one(
        {"postcard_id": postcard_id},
        {"$set": {
            "receiver_id": receiver,
            "sent_date": datetime.utcnow(),
            "status": "traveling"
        }}
    )

    # 🧾 Log transaction
    txn = {
        "txn_id": str(ObjectId()),
        "postcard_id": postcard_id,
        "sender_id": sender,
        "receiver_id": receiver,
        "timestamp": datetime.utcnow(),
        "status": "traveling"
    }
    db.transactions.insert_one(txn)

    # 🧮 Update sender’s history
    db.users.update_one(
        {"username": sender},
        {"$inc": {"sent_count": 1}, "$push": {"postcards_sent": postcard_id}}
    )

    # 🔁 Try reciprocal matching
    pending = db.postcards.find_one({"status": "pending", "sender_id": {"$ne": sender}})

    reciprocal_msg = ""
    if pending:
        db.postcards.update_one(
            {"postcard_id": pending["postcard_id"]},
            {"$set": {
                "receiver_id": sender,
                "status": "traveling",
                "sent_date": datetime.utcnow()
            }}
        )
        db.users.update_one(
            {"username": sender},
            {"$inc": {"received_count": 1}, "$push": {"postcards_received": pending["postcard_id"]}}
        )
        reciprocal_msg = f"📬 You’ll soon receive postcard '{pending['postcard_id']}' from {pending['sender_id']}!"
    else:
        reciprocal_msg = "⚠️ No other pending postcards available for reciprocal sending."

    return jsonify({
        "message": f"📮 Postcard '{postcard_id}' is now traveling to {receiver}! {reciprocal_msg}"
    }), 200

@app.route("/receive_postcard", methods=["POST"])
def receive_postcard():
    user = request.form.get("user")
    postcard_id = request.form.get("postcard_id")

    if not user or not postcard_id:
        return jsonify({"error": "User and postcard_id are required"}), 400

    postcard = db.postcards.find_one({"postcard_id": postcard_id})
    if not postcard:
        return jsonify({"error": f"Postcard '{postcard_id}' not found"}), 404
    if postcard["receiver_id"] != user:
        return jsonify({"error": f"Postcard '{postcard_id}' is not assigned to '{user}'"}), 403
    if postcard["status"] == "received":
        return jsonify({"message": f"📬 Postcard '{postcard_id}' already marked as received."}), 200

    # ✅ Update postcard status
    db.postcards.update_one(
        {"postcard_id": postcard_id},
        {"$set": {"status": "received", "received_date": datetime.utcnow()}}
    )

    # ✅ Update receiver stats
    db.users.update_one(
        {"username": user},
        {"$inc": {"received_count": 1}, "$push": {"postcards_received": postcard_id}}
    )

    # ✅ Log transaction
    db.transactions.insert_one({
        "txn_id": str(ObjectId()),
        "postcard_id": postcard_id,
        "sender_id": postcard["sender_id"],
        "receiver_id": user,
        "timestamp": datetime.utcnow(),
        "status": "received"
    })

    return jsonify({"message": f"✅ Postcard '{postcard_id}' marked as received by {user}!"}), 200


# ---------------- PROFILE ROUTE ---------------- #

@app.route("/profile", methods=["GET"])
def get_profile():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400

    user = db.users.find_one({"username": username.strip()})
    if not user:
        return jsonify({"error": f"User '{username.strip()}' not found"}), 404

    # Get postcards by status
    sent = list(db.postcards.find(
        {"sender_id": username.strip()},
        {"_id": 0, "postcard_id": 1, "receiver_id": 1, "status": 1}
    ))

    received = list(db.postcards.find(
        {"receiver_id": username.strip()},
        {"_id": 0, "postcard_id": 1, "sender_id": 1, "status": 1}
    ))

    traveling = list(db.postcards.find(
        {"sender_id": username.strip(), "status": "traveling"},
        {"_id": 0, "postcard_id": 1, "receiver_id": 1, "status": 1}
    ))

    # Build profile data
    profile_data = {
        "user_id": str(user.get("_id")),
        "username": user.get("username"),
        "email": user.get("email"),
        "address": user.get("address"),
        "country": user.get("country"),
        "registered_date": user.get("registered_date"),
        "postcards_sent": sent,
        "postcards_received": received,
        "postcards_traveling": traveling,
        "sent_count": len(sent),
        "received_count": len(received),
        "traveling_count": len(traveling)
    }

    return jsonify({
        "profile": profile_data,
        "stats": {
            "total_postcards": len(sent) + len(received) + len(traveling),
            "sent": len(sent),
            "received": len(received),
            "traveling": len(traveling)
        }
    }), 200

# ---------------- VIEW POSTCARDS ---------------- #

@app.route("/view_postcards", methods=["POST"])
def view_postcards():
    user = request.form.get("user") or (request.get_json(silent=True) or {}).get("user")
    if not user:
        return jsonify({"error": "User required"}), 400

    # 📬 Sent postcards
    sent = list(db.postcards.find(
        {"sender_id": user, "status": {"$in": ["sent", "traveling"]}},
        {"_id": 0, "postcard_id": 1, "receiver_id": 1, "status": 1, "message": 1}
    ))

    # 📥 Received postcards
    received = list(db.postcards.find(
        {"receiver_id": user, "status": "received"},
        {"_id": 0, "postcard_id": 1, "sender_id": 1, "status": 1, "message": 1}
    ))

    # 🚚 Traveling postcards (those the user will receive but haven’t yet)
    traveling = list(db.postcards.find(
        {"receiver_id": user, "status": "traveling"},
        {"_id": 0, "postcard_id": 1, "sender_id": 1, "status": 1, "message": 1}
    ))

    return jsonify({
        "sent": sent,
        "traveling": traveling,
        "received": received
    }), 200


# ---------------- FRONTEND ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    print("✅ Flask app running on http://127.0.0.1:5000")
    app.run(debug=True)
