import re

from flask import Flask, render_template, redirect, url_for, request, session
import sqlite3

app = Flask(__name__)

app.secret_key = "AAA"

def get_db_connection():
    conn = sqlite3.connect('pedare_air.db') ##connects to pedare_air db
    conn.row_factory = sqlite3.Row ##row factory helps sqlite lock on to rows in db, pull out as objects
    return conn ##return w/ function, brings output (conn is output)

def get_all_cities():
    # Fetches a clean, sorted list of all unique origin cities in the database.
    conn = get_db_connection()
    cities_query = 'SELECT DISTINCT origin FROM flights ORDER BY origin ASC' #ascending

    # Extract the string value from each row row['origin']
    db_cities = [row['origin'] for row in  
    conn.execute(cities_query).fetchall()]
    conn.close()
    return db_cities

def get_all_destinations():
    # Fetches a clean, sorted list of all unique destination cities in the database.
    conn = get_db_connection()
    dests_query = 'SELECT DISTINCT destination FROM flights ORDER BY origin ASC' #ascending

    # Extract the string value from each row row['origin']
    db_dests = [row['destination'] for row in 
    conn.execute(dests_query).fetchall()]
    conn.close()
    return db_dests

## wtf is a route
@app.route('/') ##'/' == homepage/dashboard #function sitting under route loads when go to route. when sitting by itself (see above), tool to use when needed
def index():
    conn = get_db_connection()
    db_flights = conn.execute('SELECT * FROM flights').fetchall()
    cities = get_all_cities()
    dests = get_all_destinations()
    conn.close() ## remember to close connection as otherwise leaves db insecure
    return render_template('index.html', flights=db_flights, cities=cities, dests=dests)

@app.route('/user', methods=['GET', 'POST'])
def user():
    conn = get_db_connection()
    if request.method == 'POST':
        first = request.form.get('first_name').strip()
        last = request.form.get('last_name').strip()
        email = request.form.get('email').strip()
        passport = request.form.get('passport').strip()
        print("Session data set!")

        #if not all(first, last, email, passport):
            #return render_template('login.html', error="Please complete all fields.")

        # 2. Insert the customer into the passengers table securely using tuple syntax
        cursor = conn.cursor()
        existing = cursor.execute(
            'SELECT passenger_id from passengers WHERE email = ? AND passport_num = ?', (email, passport)
        ).fetchone()

        if existing:
            passenger_id = existing["passenger_id"]
        else:
            cursor.execute('''
            INSERT INTO passengers (first_name, last_name, email, passport_num)
            VALUES (?, ?, ?, ?)
            ''', (first, last, email, passport))
            passenger_id = cursor.lastrowid

        session["passenger_id"] = passenger_id
        session["first"] = first
        session["last"] = last
        session["email"] = email
        session["passport"] = passport
        conn.commit()
        conn.close()
        return redirect(url_for('myflights'))

    else:
        return render_template('login.html')

## e.g. /book/Q3540
@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    conn = get_db_connection()

    if "passenger_id" not in session:
        conn.close()
        return redirect(url_for('user'))

    if request.method == "POST":
        passenger_id = session["passenger_id"]

        # 3. Create a matching record in the bookings table to link passenger to flight
        # For now, we will assign a random seat placeholder like '12A'
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO bookings (flight_id, passenger_id, seat_assignment)
        VALUES (?, ?, ?)
        ''', (flight_id, passenger_id, '12A'))

        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 4. Redirect back to the homepage after a successful database save
        return redirect(url_for('booking_confirmation', booking_id=booking_id))

    ## if they didn't come from booking form page
    else:
        # GET Request: Fetch the details of the specific flight to show on the form page
        flight = conn.execute('SELECT * FROM flights WHERE flight_id = ?', (flight_id,)).fetchone()
        conn.close()

        # Render the template and pass the specific flight object to it
        return render_template('booking.html', flight=flight)

@app.route('/confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    conn = get_db_connection()
    query = '''
            SELECT b.booking_id, b.seat_assignment, p.first_name, p.last_name, 
                   f.origin, f.destination, f.departure_time, f.flight_id
            FROM bookings b
            JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.booking_id = ?
        '''

    booking_details = conn.execute(query, (booking_id,)).fetchone()
    conn.close()
    
    if booking_details is None:
        return "Booking Not Found", 404

    return render_template('booking_confirmation.html', booking=booking_details)

@app.route('/myflights')
def myflights():
    if "passenger_id" not in session:
        return redirect(url_for('user'))

    passenger_id = session["passenger_id"]
    conn = get_db_connection()

    flights = conn.execute('''
        SELECT flights.* 
        FROM flights
        JOIN bookings ON flights.flight_id = bookings.flight_id
        WHERE bookings.passenger_id = ?
    ''', (passenger_id,)).fetchall()

    conn.close()
    return render_template('myflights.html', flights=flights)

if __name__ == '__main__':
    app.run(debug=True, port=8000)