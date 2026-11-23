
from app.engines.recommendation_engine import recommend_options


# Sample feasible facilities for testing sorting
sample_options = [
    {
        "facility": {
            "facility_name": "Football Ground A",
            "capacity": 60,
            "location": "North Campus"
        },
        "equipment_options": []
    },
    {
        "facility": {
            "facility_name": "Football Ground B",
            "capacity": 30,
            "location": "South Campus"
        },
        "equipment_options": []
    },
    {
        "facility": {
            "facility_name": "Football Ground C",
            "capacity": 45,
            "location": "East Campus"
        },
        "equipment_options": []
    }
]


print("\n========== RECOMMENDATION SORTING TEST ==========")

print("\nBEFORE SORTING:")

for option in sample_options:
    facility = option["facility"]
    print(facility["facility_name"], "| Capacity:", facility["capacity"])


recommendations = recommend_options(sample_options)

print("\nAFTER SORTING:")

for index, option in enumerate(recommendations, start=1):
    facility = option["facility"]

    print(
        "Recommendation", index,
        "|", facility["facility_name"],
        "| Capacity:", facility["capacity"],
        "| Location:", facility["location"]
    )

print("\nRECOMMENDATION SORTING TEST COMPLETED!")
