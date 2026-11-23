
from app.database.connection import engine

try:
    with engine.connect() as connection:
        print("SportSync MySQL connection successful!")
        print("Database:", connection.engine.url.database)

except Exception as error:
    print("Database connection failed!")
    print(error)
