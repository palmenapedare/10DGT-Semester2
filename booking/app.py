from flask import Flask, render_template, redirect, url_for, request
import sqlite3

app = Flask(__name__)

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

## wtf is a route
@app.route('/') ##'/' == homepage/dashboard #function sitting under route loads when go to route. when sitting by itself (see above), tool to use when needed
def index():
    conn = get_db_connection()
    db_flights = conn.execute('SELECT * FROM flights').fetchall()
    conn.close() ## remember to close connection as otherwise leaves db insecure
    return render_template('index.html', flights=db_flights)

## e.g. /book/Q3540
@app.route('/book/<int:flight_id>', methods=['GET', 'POST'])
def book_flight(flight_id):
    conn = get_db_connection()

    if request.method == 'POST':
        # 1. Capture the form text inputs using the HTML 'name' attributes
        first = request.form.get('first_name')
        last = request.form.get('last_name')
        email = request.form.get('email')
        passport = request.form.get('passport')

        # 2. Insert the customer into the passengers table securely using tuple syntax
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO passengers (first_name, last_name, email, passport_num)
            VALUES (?, ?, ?, ?)
        ''', (first, last, email, passport))
        
        # Grab the auto-generated passenger_id of the person we just inserted
        passenger_id = cursor.lastrowid

        # 3. Create a matching record in the bookings table to link passenger to flight
        # For now, we will assign a random seat placeholder like '12A'
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
    
    # SQL JOIN to grab Passenger, Flight, and Booking details in one query
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

if __name__ == '__main__':
    app.run(debug=True)