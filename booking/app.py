from random import random
from functools import wraps

from flask import Flask, jsonify, render_template, redirect, url_for, request, session
import sqlite3
import re
from datetime import date, timedelta

app = Flask(__name__)

app.secret_key = "AAA"

adminpassword = '1234' 

def get_db_connection():
    conn = sqlite3.connect('pedare_air.db') ##connects to pedare_air db
    conn.row_factory = sqlite3.Row ##row factory helps sqlite lock on to rows in db, pull out as objects
    booking_columns = conn.execute('PRAGMA table_info(bookings)').fetchall()
    existing_columns = {column['name'] for column in booking_columns}
    for column_name in ('seat2', 'seat3', 'seat4'):
        if booking_columns and column_name not in existing_columns:
            conn.execute(f'ALTER TABLE bookings ADD COLUMN {column_name} TEXT')
    if booking_columns:
        conn.commit()
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

def get_all_passengers():
    # Fetches all passengers in alphabetical order.
    conn = get_db_connection()
    passengers_query = '''
        SELECT passenger_id, first_name, last_name, email, passport_num
        FROM passengers
        ORDER BY first_name ASC
    '''

    db_passengers = conn.execute(passengers_query).fetchall()
    conn.close()
    return db_passengers #!!!!! fix

def get_booked_seats(flight_id=None):
    conn = get_db_connection()
    if flight_id is None:
        flight_id = request.args.get('flight_id')

    if flight_id is None:
        rows = conn.execute(
                '''SELECT seat_assignment, seat2, seat3, seat4
                    FROM bookings WHERE seat_assignment IS NOT NULL'''
        ).fetchall()
    else:
        rows = conn.execute(
                '''SELECT seat_assignment, seat2, seat3, seat4
                    FROM bookings WHERE seat_assignment IS NOT NULL AND flight_id = ?''',
            (flight_id,)
        ).fetchall()
    conn.close()
    return [seat for row in rows for seat in (
        row['seat_assignment'], row['seat2'], row['seat3'], row['seat4']
    ) if seat]

def get_booking_number():
    conn = get_db_connection()
    bookingnumber = 0
    rows = conn.execute(
        'SELECT booking_id FROM bookings'
    ).fetchall()
    conn.close()
    for i in rows:
        bookingnumber = +1

@app.route('/api/booked-seats')
def api_booked_seats():
    return jsonify(get_booked_seats())

def login_required(function):
    @wraps(function)
    def secure_function(*args, **kwargs):
        if "password" not in session:
            return redirect(url_for("adminlogin"))
        return function()
    return secure_function

@app.route('/') ##'/' == homepage/dashboard #function sitting under route loads when go to route. when sitting by itself (see above), tool to use when needed
def index():
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    flight_date = request.args.get('date', '').strip()

    session['search_origin'] = origin
    session['search_destination'] = destination
    session['search_date'] = flight_date

    todaysdate = date.today()
    tomorrow = todaysdate + timedelta(days=1)

    conn = get_db_connection()
    query = '''
        SELECT
            f.flight_id,
            f.origin,
            f.destination,
            f.departure_time,
            f.capacity,
            CASE
                WHEN substr(f.departure_time, 1, 10) IN (?, ?)
                THEN f.price * 0.5
                ELSE f.price
            END AS price,
            CASE
                WHEN substr(f.departure_time, 1, 10) IN (?, ?)
                THEN 1
                ELSE 0
            END AS timebasedsale,
            COUNT(b.booking_id) AS passengers_booked,
            f.capacity - COUNT(b.booking_id) AS seats_remaining,
            CASE
                WHEN f.capacity - COUNT(b.booking_id) <= 0 THEN 1
                ELSE 0
            END AS soldout
        FROM flights AS f
        LEFT JOIN bookings AS b ON b.flight_id = f.flight_id
    '''

    filters = []
    values = [
        todaysdate.isoformat(), tomorrow.isoformat(),
        todaysdate.isoformat(), tomorrow.isoformat()
    ]

    if origin:
        filters.append('f.origin = ?')
        values.append(origin)
    if destination:
        filters.append('f.destination = ?')
        values.append(destination)
    if flight_date:
        filters.append('substr(f.departure_time, 1, 10) = ?')
        values.append(flight_date)

    if filters:
        query += ' WHERE ' + ' AND '.join(filters)

    query += ' GROUP BY f.flight_id, f.origin, f.destination, f.departure_time, f.capacity, f.price ORDER BY f.departure_time ASC'

    db_flights = conn.execute(query, values).fetchall()
    cities = get_all_cities()
    dests = get_all_destinations()
    conn.close() ## remember to close connection as otherwise leaves db insecure
    return render_template(
        'index.html',
        flights=db_flights,
        cities=cities,
        dests=dests,
        selected_origin=origin,
        selected_destination=destination,
        selected_date=flight_date,
    )

@app.route('/login', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))

    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    return render_template('logout.html')

@app.route('/logoutconfirmation')
def logoutconfirmation():
    session.clear()
    return render_template('logoutconfirmation.html')

## e.g. /book/Q3540
@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    conn = get_db_connection()

    if "passenger_id" not in session:
        conn.close()
        return redirect(url_for('user'))

    if request.method == "POST":
        passenger_id = session["passenger_id"]
        seat_choice = request.form.get('seat_choice')
        if seat_choice == 'yes':
            return redirect(url_for('seats', flight_id=flight_id))

        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO bookings (flight_id, passenger_id, seat_assignment)
        VALUES (?, ?, ?)
        ''', (flight_id, passenger_id, '12A'))
        session["bookingnumber"] = +1
        bookingnumber = +1

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
                 SELECT b.booking_id, b.seat_assignment, b.seat2, b.seat3, b.seat4,
                     p.first_name, p.last_name,
                   f.origin, f.destination, f.departure_time, f.flight_id
            FROM bookings b
            LEFT JOIN passengers p ON b.passenger_id = p.passenger_id
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.booking_id = ?
        '''

    booking_details = conn.execute(query, (booking_id,)).fetchone()
    conn.close()
    
    if booking_details is None:
        return "Booking Not Found", 404

    return render_template('booking_confirmation.html', booking=booking_details)

@app.route('/seats/<int:flight_id>', methods=['GET', 'POST'])
def seats(flight_id):
    conn = get_db_connection()
    get_booked_seats()
    if request.method == 'POST':
        if 'passenger_id' not in session:
            conn.close()
            return redirect(url_for('user'))

        passenger = conn.execute(
            'SELECT passenger_id FROM passengers WHERE passenger_id = ?',
            (session['passenger_id'],)
        ).fetchone()
        if passenger is None:
            session.pop('passenger_id', None)
            conn.close()
            return redirect(url_for('user'))

        selected_seats = [request.form.get(name, '').strip() for name in (
            'selected_seat', 'selected_seat2', 'selected_seat3', 'selected_seat4'
        )]
        selected_seats = [seat for seat in selected_seats if seat]
        if not selected_seats:
            conn.close()
            return redirect(url_for('seats', flight_id=flight_id))

        cursor = conn.cursor()
        existing = cursor.execute(
            'SELECT booking_id FROM bookings WHERE flight_id = ? AND passenger_id = ?',
            (flight_id, session['passenger_id'])
        ).fetchone()

        if existing:
            cursor.execute(
                     '''UPDATE bookings
                         SET seat_assignment = ?, seat2 = ?, seat3 = ?, seat4 = ?
                         WHERE booking_id = ?''',
                     (*selected_seats, *(None,) * (4 - len(selected_seats)), existing['booking_id'])
            )
            booking_id = existing['booking_id']
        else:
            cursor.execute(
                     '''INSERT INTO bookings
                         (flight_id, passenger_id, seat_assignment, seat2, seat3, seat4)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                     (flight_id, session['passenger_id'], *selected_seats, *(None,) * (4 - len(selected_seats)))
            )
            booking_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return redirect(url_for('booking_confirmation', booking_id=booking_id))

    flight = conn.execute('SELECT * FROM flights WHERE flight_id = ?', (flight_id,)).fetchone()
    if flight is None:
        conn.close()
        return 'Flight not found', 404

    airplane_type = flight['airplane_type']
    booked_seats = conn.execute(
          '''SELECT seat_assignment, seat2, seat3, seat4
              FROM bookings WHERE flight_id = ?''',
        (flight_id,)
    ).fetchall()
    booked_seats_list = [seat for row in booked_seats for seat in (
        row['seat_assignment'], row['seat2'], row['seat3'], row['seat4']
    ) if seat]
    conn.close()

    if airplane_type in ('Airbus A320', 'Airbus A330'):
        return render_template('airbusseats.html', flight=flight, booked_seats=booked_seats_list)
    elif airplane_type == 'Boeing 737':
        return render_template('boeingseats.html', flight=flight, booked_seats=booked_seats_list)
    else:
        return f'Unknown airplane type: {airplane_type}', 400

@app.route('/myflights')
def myflights():
    if "passenger_id" not in session:
        return redirect(url_for('user'))

    passenger_id = session["passenger_id"]
    conn = get_db_connection()

    flights = conn.execute('''
         SELECT flights.*, bookings.seat_assignment, bookings.seat2,
             bookings.seat3, bookings.seat4
        FROM flights
        JOIN bookings ON flights.flight_id = bookings.flight_id
        WHERE bookings.passenger_id = ?
    ''', (passenger_id,)).fetchall()

    conn.close()
    return render_template('myflights.html', flights=flights,)

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == adminpassword:
            session["password"] = password
            return redirect('/admin')
        else:
            return render_template('adminlogin.html', error="Incorrect password. Please try again.")
    else:
        return render_template('adminlogin.html', error=None)

@app.route('/admin')
@login_required
def admin():
    passengers = get_all_passengers()
    conn = get_db_connection()
    bookingnumber = get_booking_number()
    flight_id = request.args.get('flight_id', '').strip()
    
    query = '''
        SELECT f.*,
               COUNT(b.booking_id) AS passengers_booked,
               f.capacity - COUNT(b.booking_id) AS seats_remaining 
        FROM flights AS f
        LEFT JOIN bookings AS b ON b.flight_id = f.flight_id
    '''
    
    if flight_id:
        query += ' WHERE f.flight_id = ?'
        query += ' GROUP BY f.flight_id ORDER BY f.flight_id ASC'
        flights = conn.execute(query, (flight_id,)).fetchall()
    else:
        query += ' GROUP BY f.flight_id ORDER BY f.flight_id ASC'
        flights = conn.execute(query).fetchall()
    passengers_booked = conn.execute(
        'SELECT COUNT(*) AS passengers_booked FROM bookings'
    ).fetchone()['passengers_booked']
    flight_quantity = conn.execute(
        'SELECT COUNT(*) AS flight_quantity FROM flights'
    ).fetchone()['flight_quantity']
    profit_earned = conn.execute(
        '''
        SELECT COALESCE(SUM(f.price), 0) AS profit_earned
        FROM bookings AS b
        JOIN flights AS f ON b.flight_id = f.flight_id
        ''').fetchone()['profit_earned']

    booking_ids = [row['booking_id'] for row in conn.execute('''
        SELECT booking_id FROM bookings
        ''').fetchall()] #order by asc? not working when I tried
    conn.close()
    return render_template('admin.html', flights=flights, passengers=passengers, flight_quantity=flight_quantity, passengers_booked=passengers_booked, profit_earned=profit_earned, booking_ids=booking_ids, bookingnumber=bookingnumber, selected_flight_id=flight_id)

@app.route('/alter', methods=['GET', 'POST'])
@app.route('/alter/<int:flight_id_alter>', methods=['GET', 'POST'])
def alter(flight_id_alter=None):
    if flight_id_alter is None:
        flight_id_alter = request.args.get('flight_id', type=int)
    if flight_id_alter is None:
        return redirect(url_for('admin'))

    conn = get_db_connection()
    flight = conn.execute(
        'SELECT * FROM flights WHERE flight_id = ?',
        (flight_id_alter,)
    ).fetchone()
    flights = conn.execute(
        '''SELECT DISTINCT flight_id FROM flights ORDER BY flight_id ASC'''
    ).fetchall()
    choice = request.form.get('change_time', '').strip()

    if request.method == 'POST' and choice == '1':
        conn.execute(
            'UPDATE flights SET status = ? WHERE flight_id = ?',
            ('Cancelled', flight_id_alter)
        )
        conn.commit()
    elif request.method == 'POST' and choice in ('2', '3'):
        alter_date = request.form.get('alter_date', '').strip()
        if not alter_date:
            conn.close()
            return render_template('alter.html', flight=flight, flights=flights, error='Please enter a new date and time.'), 400

        alter_date = alter_date.replace('T', ' ')
        conn.execute(
            '''UPDATE flights
               SET departure_time = ?, status = ?
               WHERE flight_id = ?''',
            (alter_date, 'Delayed' if choice == '2' else 'Rescheduled', flight_id_alter)
        )
        conn.commit()

    conn.close()
    if flight is None:
        return 'Flight not found', 404

    if request.method == 'POST':
        return redirect(url_for('alter', flight_id_alter=flight_id_alter))
    return render_template('alter.html', flight=flight, flights=flights)

if __name__ == '__main__':
    app.run(debug=True, port=8000) #added port as error was happening and keeping it consistent fixed it. don't know why