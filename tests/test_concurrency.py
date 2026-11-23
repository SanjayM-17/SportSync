
import requests
import concurrent.futures
import time

URL = "http://127.0.0.1:8000/bookings/confirm"

def send_booking(user_id):
    payload = {
        "user_id": user_id,
        "sport": "Football",
        "participants": 20,
        "booking_date": "2018-01-01",
        "start_time": "07:00",
        "end_time": "08:00",
        "facility_id": "F001",
        "equipment_id": "E002",
        "equipment_quantity": 5
    }

    return requests.post(URL, json=payload, timeout=30)


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
    future1 = executor.submit(send_booking, "U0001")
    future2 = executor.submit(send_booking, "U0002")

    response1 = future1.result()
    response2 = future2.result()

print("USER U0001:", response1.status_code, response1.json())
print("USER U0002:", response2.status_code, response2.json())
