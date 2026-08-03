from flask import Flask, render_template

app = Flask(__name__)

@app.route('/') #'/' == homepage/dashboard
def index():
    # START CODE: Currently hardcoded. 
    # TASK: Students will eventually fetch this from SQLite/Faker.
    sample_flights = [
        {"id": 1, "origin": "Adelaide", "dest": "Melbourne", "date": "2024-11-12", "price": 89, "time": "14:20"},
        {"id": 2, "origin": "Adelaide", "dest": "Sydney", "date": "2024-11-12", "price": 124, "time": "10:05"},
        {"id": 3, "origin": "Adelaide", "dest": "Gold Coast", "date": "2024-11-13", "price": 156, "time": "08:30"} #this needs to come from database
    ]
    return render_template('index.html', flights=sample_flights)

if __name__ == '__main__':
    app.run(debug=True)