
from app.engines.recommendation_engine import recommend_options


print("\n========== RECOMMENDATION TEST CASES ==========")

# TC01: Empty options
result = recommend_options([])
print("\nTC01 - Empty options:", "PASS" if result == [] else "FAIL")


# TC02: Equal capacity
equal_options = [
    {
        "facility": {
            "facility_name": "Ground B",
            "capacity": 40
        },
        "equipment_options": []
    },
    {
        "facility": {
            "facility_name": "Ground A",
            "capacity": 40
        },
        "equipment_options": []
    }
]

result = recommend_options(equal_options)

expected = ["Ground A", "Ground B"]
actual = [
    item["facility"]["facility_name"]
    for item in result
]

print(
    "\nTC02 - Equal capacity:",
    "PASS" if actual == expected else "FAIL"
)


# TC03: Different capacities
different_options = [
    {
        "facility": {"facility_name": "Ground C", "capacity": 60},
        "equipment_options": []
    },
    {
        "facility": {"facility_name": "Ground A", "capacity": 20},
        "equipment_options": []
    },
    {
        "facility": {"facility_name": "Ground B", "capacity": 40},
        "equipment_options": []
    }
]

result = recommend_options(different_options)

actual = [
    item["facility"]["capacity"]
    for item in result
]

print(
    "\nTC03 - Different capacities:",
    "PASS" if actual == [20, 40, 60] else "FAIL"
)

print("\nRECOMMENDATION TESTING COMPLETED!")
