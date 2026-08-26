# TALK TO MR JUPE ABOUT DIFFICULTY WITH python [name].py 'no such file or directory' as terminal autofill doesnt include 'booking' folder
    #then open in db browser for sqlite

import sqlite3 #language for talking to database
import random
from faker import Faker #generate fake details

# 1. Setup SQLite and Faker

fake = Faker('en_AU')  # Uses the Australian locale for realistic names/cities
connection = sqlite3.connect('pedare_air.db')
cursor = connection.cursor()

print("🌱 Starting database seeding...")

# 2. Recreate Tables (Drop first so running the script multiple times clears old data)
cursor.execute("DROP TABLE IF EXISTS bookings") ##cursor.execute is talking to database
cursor.execute("DROP TABLE IF EXISTS passengers")
cursor.execute("DROP TABLE IF EXISTS flights")

cursor.execute('''
    CREATE TABLE flights (
        flight_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        origin TEXT,
        destination TEXT,
        departure_time TEXT,
        capacity INTEGER,
        price INTEGER
        airplane_type TEXT
    )
''')

cursor.execute('''
    CREATE TABLE passengers (
        passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        email TEXT,
        passport_num TEXT
    ) 
''')

cursor.execute('''
    CREATE TABLE bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER,
        passenger_id INTEGER,
        seat_assignment TEXT,
        date_booked TEXT,
        FOREIGN KEY(flight_id) REFERENCES flights(flight_id),
        FOREIGN KEY(passenger_id) REFERENCES    passengers(passenger_id)
    ) 
''')

# 3. Generate Flights Data
cities = ['Adelaide', 'Melbourne', 'Sydney', 'Brisbane', 'Perth', 'Gold Coast']

print("-> Generating flights...")
for _ in range(12): ##generate 12 flights
    # Ensure origin and destination aren't the same city
    origin, destination = random.sample(cities, 2) ##generate an origin and a dest.
    
    # Generate a random future flight time inside a window of 2026
    departure_time = fake.future_datetime(end_date='+30d').strftime('%Y-%m-%d %H:%M')
    price = random.choice([79, 99, 129, 149, 199, 249])
    airplane_type = fake.airline.airplane()
    capacity = random.choice([150, 180, 220]) # Standard Airbus/Boeing sizes
    
    cursor.execute('''
        INSERT INTO flights (origin, destination, departure_time, capacity, price, airplane_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (origin, destination, departure_time, capacity, price, airplane_type))

# 4. Generate Passengers Data
print("-> Generating 50 unique passengers...")
for _ in range(50):
    first_name = fake.first_name()
    last_name = fake.last_name()
    # Create an email based on their actual fake name
    email = f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}"
    # Australian Passport format: 1 letter followed by 7 digits
    passport_num = fake.bothify(text='?#######').upper() #? is letter, # is number
    
    cursor.execute('''
        INSERT INTO passengers (first_name, last_name, email, passport_num)
        VALUES (?, ?, ?, ?)
    ''', (first_name, last_name, email, passport_num))

# 5. Generate a few existing Bookings (To show data on day one)
print("-> Linking passengers to flights...")
for passenger_id in range(1, 15): # Let's book the first 14 passengers onto random flights
    flight_id = random.randint(1, 12)
    seat = fake.airline.seat({ airplaneType: airplane_type })
    date_listed = random_date = fake.date_between(start_date="-1y", end_date="today").strftime("%Y-%m-%d")

    cursor.execute('''
        INSERT INTO bookings (flight_id, passenger_id, seat_assignment, date_booked)
        VALUES (?, ?, ?, ?)
    ''', (flight_id, passenger_id, seat, date_listed))

# Commit updates and close out
connection.commit()
connection.close()

print("✨ Database successfully seeded with Australian context data!")