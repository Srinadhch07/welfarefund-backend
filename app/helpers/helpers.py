import random
from bson import ObjectId
import json
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import json, ast
import random

def generate_random_text():
    chars = "abcdefghijklmnopqrstyouvxyz1234567890"
    return ''.join(random.choice(chars) for _ in range(10))

def generate_otp(length=6):
    if length <= 0:
        raise ValueError("OTP length must be greater than 0")
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

def convert_objectids(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [convert_objectids(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_objectids(v) for k, v in obj.items()}
    else:
        return obj

def safe_json_loads(s):
    try:
        if isinstance(s, dict):
            return s
        return json.loads(s)

    except json.JSONDecodeError:
        try:
           
            return ast.literal_eval(s)
        except Exception:
            print(f"Failed to parse JSON: {s}")
            return {"raw_content": s}

def safe_json(data):
    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, ObjectId):
            return str(o)
        return str(o)
    return json.dumps(data, ensure_ascii=False, default=default)

def serialize_doc(doc):
    if not doc:
        return doc

    serialized = {}

    for key, value in doc.items():

        # Convert ObjectId
        if isinstance(value, ObjectId):
            serialized[key] = str(value)

        # Convert datetime
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()

        # Convert nested dict
        elif isinstance(value, dict):
            serialized[key] = serialize_doc(value)

        # Convert list of objects
        elif isinstance(value, list):
            serialized[key] = [serialize_doc(item) if isinstance(item, dict) else (
                str(item) if isinstance(item, ObjectId) else item
            ) for item in value]

        else:
            serialized[key] = value

    return serialized

def serialize_docs(docs):
    return [serialize_doc(doc) for doc in docs]

def is_valid_objectid(id_str: str) -> bool:
    try:
        ObjectId(id_str)
        pass
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

def count_words(text: str) -> int:
    return len(text.split())

def utc_to_ist(utc_str: str):
    dt = datetime.strptime(utc_str, "%Y-%m-%dT%H:%MZ")
    return dt + timedelta(hours=5, minutes=30)

def to_ist(dt):
    return dt + timedelta(hours=5, minutes=30)

def is_private_email(email: str) -> bool:
    return email.endswith("privaterelay.appleid.com")

