# SportSync – Smart Campus Sports Resource Allocation, Scheduling and Recommendation System

## 1. Project Overview

SportSync is a smart campus sports resource allocation and booking system designed to simplify the reservation of sports facilities and equipment within a college campus.

The system helps students and other authorised users find suitable sports facilities, check availability, detect booking conflicts and receive alternative recommendations.

It aims to reduce manual booking effort, prevent overlapping confirmed bookings and maintain consistent booking and equipment records.

## 2. Problem Statement

Traditional campus sports booking processes often involve manual searching and checking of facilities, time slots and equipment. This can result in:

- Repeated searching for available facilities.
- Difficulty identifying suitable alternatives.
- Facility and equipment availability conflicts.
- Risk of duplicate or overlapping bookings.
- Inconsistent booking records.

SportSync addresses these problems through progressive filtering, conflict detection, alternative recommendations and controlled booking confirmation.

## 3. Project Objectives

- Provide a structured sports resource booking process.
- Filter facilities based on sport compatibility and participant capacity.
- Check facility, time-slot and equipment availability.
- Detect booking conflicts.
- Recommend suitable alternative resources.
- Maintain consistent booking and equipment records.
- Control concurrent booking confirmation requests.

## 4. System Workflow

The booking process follows these steps:

1. Select Sport.
2. Enter Number of Participants.
3. Select Facility.
4. Select Available Time Slot.
5. Select Equipment.
6. Enter Equipment Quantity.
7. Review Booking Details.
8. Verify Availability.
9. Confirm Booking.

Only available options are presented during the selection process. Final availability is checked again during booking confirmation.

## 5. Engine Architecture

SportSync is organised into four major engines.

### Engine 1 – Progressive Filtering, Conflict Detection and Alternative Recommendation (DSA)

**Responsibility:** Sanjay M

- Filters facilities based on sport compatibility.
- Checks participant capacity.
- Evaluates time-slot availability.
- Checks equipment compatibility and quantity.
- Detects resource and booking conflicts.
- Generates alternative facility and equipment recommendations.

**Main files:**
- `app/engines/filtering_engine.py`
- `app/engines/dsa_engine.py`
- `app/engines/conflict_engine.py`
- `app/engines/recommendation_engine.py`

### Engine 2 – Booking Transaction and Data Consistency (DBMS)

**Responsibility:** Vinayak W

- Manages booking confirmation.
- Maintains persistent booking records.
- Revalidates resource availability before confirmation.
- Uses database transactions.
- Maintains equipment quantity consistency.
- Prevents duplicate requests using unique request IDs.

**Main files:**
- `app/services/booking_service.py`
- `app/services/booking_confirmation.py`
- `app/database/connection.py`

### Engine 3 – Concurrency Control (OS)

**Responsibility:** Vrushabh B

- Controls concurrent booking operations.
- Uses resource locks to coordinate access.
- Acquires resource locks in sorted order.
- Uses database-level locking during confirmation.
- Helps prevent conflicting simultaneous confirmations.

**Main file:**
- `app/engines/os_engine.py`

### Engine 4 – Guided Selection and Access Control (Web)

**Responsibility:** Prajwal P

- Provides API endpoints for the guided booking process.
- Handles requests for sports, facilities, time slots and equipment.
- Provides recommendation and confirmation endpoints.
- Supports the application access workflow.

**Main files:**
- `app/main.py`
- `app/routers/booking.py`
- `app/schemas/booking.py`

## 6. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Database | MySQL 8 |
| ORM | SQLAlchemy |
| Database Driver | PyMySQL |
| API Documentation | Swagger UI |
| Testing | Python testing utilities |
| Version Control | Git and GitHub |

## 7. Project Structure

```text
SportSync/
│
├── app/
│   ├── main.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── check_data.py
│   │   └── test_connection.py
│   │
│   ├── engines/
│   │   ├── conflict_engine.py
│   │   ├── dsa_engine.py
│   │   ├── filtering_engine.py
│   │   ├── os_engine.py
│   │   └── recommendation_engine.py
│   │
│   ├── routers/
│   │   └── booking.py
│   │
│   ├── schemas/
│   │   └── booking.py
│   │
│   └── services/
│       ├── booking_confirmation.py
│       └── booking_service.py
│
├── tests/
│
├── evidence/
│   ├── screenshots/
│   ├── test-results/
│   ├── api-outputs/
│   └── logs/
│
├── requirements.txt
├── .env
└── README.md
```

## 8. Installation and Setup

### Prerequisites

Install the following:

- Python 3.14.7
- MySQL Server 8.0
- Git
- Visual Studio Code or another Python IDE

### Step 1 – Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Navigate into the project directory:

```bash
cd SportSync
```

### Step 2 – Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 3 – Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 – Configure MySQL

Start the MySQL service and create the project database.

Configure the database connection details in the `.env` file according to the settings expected by `app/database/connection.py`.

Example configuration:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=sportsync
```

Do not upload your actual `.env` file or database credentials to GitHub.

### Step 5 – Run the Backend

From the project root directory:

```bash
uvicorn app.main:app --reload
```

The backend server will run at:

```text
http://127.0.0.1:8000
```

## 9. API Endpoints

The following endpoints support the guided booking workflow.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/bookings/sports` | Retrieve available sports |
| POST | `/bookings/facilities` | Retrieve suitable facilities |
| POST | `/bookings/timeslots` | Retrieve available time slots |
| POST | `/bookings/equipment` | Retrieve suitable equipment |
| POST | `/bookings/recommend` | Generate alternative recommendations |
| POST | `/bookings/confirm` | Confirm a booking |

### Swagger API Documentation

Open the following URL after starting the backend:

http://127.0.0.1:8000/docs

Swagger UI can be used to inspect and test the API endpoints.

## 10. Booking Conflict Handling

SportSync checks for conflicts before confirming a booking.

The main conflict categories are:

- **Capacity Conflict:** The number of participants exceeds the facility capacity.
- **Facility/Resource Conflict:** A facility or resource is unavailable.
- **Equipment Conflict:** Requested equipment quantity exceeds available stock.

Confirmed bookings are checked for overlapping time intervals across the campus.

The booking confirmation process performs a final availability check before saving the booking.

## 11. Database and Concurrency Management

The project uses MySQL with InnoDB transactions.

The booking confirmation implementation uses:

- READ COMMITTED transaction isolation.
- Pessimistic locking through `SELECT ... FOR UPDATE`.
- A campus-wide booking-control row and relevant resource records.
- Unique request IDs for duplicate-request protection.
- Transaction commit and rollback operations.

The OS engine also uses process-level resource locks to coordinate operations within the running application process.

## 12. Testing and Validation

The following component test results have been obtained:

| Component | Test Cases Passed |
|---|---:|
| DSA Filtering | 5/5 |
| Recommendation Engine | 3/3 |
| Conflict Detection | 4/4 |
| Pydantic Validation | 6/6 |
| Booking Confirmation | 7/7 |

Additional validation performed:

- Successful booking confirmation.
- Duplicate request handling.
- Rejection of overlapping booking requests.
- Equipment quantity validation.
- Database record verification.
- API endpoint testing.

Detailed test outputs and screenshots should be maintained in the `evidence/` directory.

**Note:** Large-scale load testing and the performance benchmark involving 500 resources and 10,000 bookings are pending. They should not be considered completed until the tests have been executed.

## 13. Current Implementation Status

| Area | Status |
|---|---|
| Progressive Filtering | Implemented |
| Conflict Detection | Implemented |
| Alternative Recommendation | Implemented |
| Booking Confirmation | Implemented |
| Database Transaction Handling | Implemented |
| Duplicate Request Protection | Implemented |
| Resource Locking | Implemented |
| API Integration | Implemented |
| Large-Scale Load Testing | Pending |
| Performance Benchmarking | Pending |
| Multi-Worker Concurrency Validation | Pending |

## 14. Future Enhancements

- Perform large-scale concurrent booking tests.
- Benchmark filtering performance with larger datasets.
- Improve fine-grained resource locking to reduce contention.
- Add comprehensive API integration tests.
- Improve monitoring and error logging.
- Complete performance validation against the defined non-functional requirements.

## 15. Team Members

| Name | Engine Responsibility |
|---|---|
| Sanjay M | E1 – DSA |
| Vinayak W | E2 – DBMS |
| Vrushabh B | E3 – OS |
| Prajwal P | E4 – Web |

**Project:** SportSync – Smart Campus Sports Resource Allocation, Scheduling and Recommendation System

**Institution:** KLE Technological University  
**Department:** School of Computer Science and Engineering

---

