
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8000/bookings/confirm"

payloads = [
    {
        "request_id": "TEST-EQUIPMENT-CONCURRENT-001",
        "user_id": "U0001",
        "sport": "Football",
        "participants": 10,
        "booking_date": "2018-01-01",
        "start_time": "07:00",
        "end_time": "08:00",
        "equipment_quantity": 10,
        "facility_id": "F001",
        "equipment_id": "E002"
    },
    {
        "request_id": "TEST-EQUIPMENT-CONCURRENT-002",
        "user_id": "U0002",
        "sport": "Football",
        "participants": 10,
        "booking_date": "2018-01-01",
        "start_time": "08:00",
        "end_time": "09:00",
        "equipment_quantity": 10,
        "facility_id": "F001",
        "equipment_id": "E002"
    }
]


def send_request(payload):
    try:
        response = requests.post(URL, json=payload, timeout=30)
        return response.status_code, response.json()
    except Exception as error:
        return "ERROR", str(error)


with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(send_request, payloads))

for index, result in enumerate(results, start=1):
    print(f"\nREQUEST {index}")
    print("Status:", result[0])
    print("Response:", result[1])
