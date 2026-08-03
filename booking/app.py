from flask import Flask, render_template, redirect, url_for, request
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('pedare_air.db') #connects to pedare_air db
    conn.row_factory = sqlite3.Row #row factory helps sqlite lock on to rows in db, pull out as objects
    return conn #return w/ function, brings output (conn is output)

def get_all_cities():
    # Fetches a clean, sorted list of all unique origin cities in the database.
    conn = get_db_connection()
    cities_query = 'SELECT DISTINCT origin FROM flights ORDER BY origin ASC' #ascending
    
    # Extract the string value from each row row['origin']
    db_cities = [row['origin'] for row in  
    conn.execute(cities_query).fetchall()]
    conn.close()
    return db_cities




@app.route('/') #'/' == homepage/dashboard #function sitting under route loads when go to route. when sitting by itself (see above), tool to use when needed
def index():
    conn = get_db_connection()
    db_flights = conn.execute('SELECT * FROM flights').fetchall()
    conn.close() #remember to close connection as otherwise leaves db insecure
    return render_template('index.html', flights=db_flights)

if __name__ == '__main__':
    app.run(debug=True)