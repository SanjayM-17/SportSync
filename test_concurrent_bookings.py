
import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8000/bookings/confirm"

requests_data = [
    {
        "sport": "Basketball",
        "participants": 12,
        "facility_id": "F002",
        "booking_date": "2018-01-02",
        "start_time": "14:00",
        "end_time": "15:00",
        "equipment_id": "E001",
        "equipment_quantity": 12,
        "request_id": "EQUIPMENT_TEST_A",
        "user_id": "U0001"
    },
    {
        "sport": "Basketball",
        "participants": 12,
        "facility_id": "F002",
        "booking_date": "2018-01-02",
        "start_time": "14:00",
        "end_time": "15:00",
        "equipment_id": "E001",
        "equipment_quantity": 12,
        "request_id": "EQUIPMENT_TEST_B",
        "user_id": "U0002"
    }
]


def submit_booking(data):
    try:
        response = requests.post(
            URL,
            json=data,
            timeout=60
        )
        return data["request_id"], response.status_code, response.json()

    except Exception as error:
        return data["request_id"], None, str(error)


print("=== CONCURRENT EQUIPMENT TEST ===")

with ThreadPoolExecutor(max_workers=2) as executor:
    results = list(executor.map(submit_booking, requests_data))

for request_id, status, response in results:
    print("\nRequest:", request_id)
    print("HTTP status:", status)
    print("Response:", response)
