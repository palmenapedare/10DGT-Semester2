from flask import Flask, render_template
import sqlite3
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import io
import base64

#DB Generator
app = Flask(__name__)
df = pd.read_csv("data.csv")
print(df)
conn = sqlite3.connect('real_estate.db')
df.to_sql(name='data', con=conn, if_exists="replace", index=False)
conn.close()

@app.route('/')
def index():
    print("index page")
    conn = sqlite3.connect('real_estate.db')
    query = '''
        SELECT
            d."Address",
            d."Sale date",
            d."Amount ($)",
            d."Bedrooms",
            d."Land Size (m^2)"
        FROM data AS d
        ORDER BY "Sale date" DESC
    '''
    database = conn.execute(query).fetchall()
    addressquery = 'SELECT DISTINCT Address FROM data ORDER BY "Sale date" ASC'
    addresslist = conn.execute(addressquery)

    conn.close()

    return render_template('index.html', database=database, addresslist=addresslist)

@app.route('/sales')
def get_sales():
    # graph 1, Address v Cost
    query = '''
           SELECT
               d."Address",
               d."Amount ($)",
           FROM data AS d
           ORDER BY "Amount ($)" ASC
       '''

    with sqlite3.connect('real_estate.db') as conn:
        database = pd.read_sql_query(query, conn)
    database["Amount ($)"] = pd.to_numeric(
        database["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )
    database = database.sort_values("Amount ($)")

    fig = Figure()
    FigureCanvasAgg(fig)
    ax = fig.subplots()
    ax.bar(database["Address"], database["Amount ($)"], label="Real Estate Sales", color="navy")
    ax.tick_params(axis="x", labelrotation=90)
    fig.tight_layout(rect=[0, 0, 0.9, 1])
    ax.set_title("Sales in TTG 5091")
    ax.set_ylabel("Amount ($, in millions)") #fix so not decimals? e.g. 700 000 = 0.7 right now

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    conn.close()

    #graph 2, Sale date v Cost
    query = '''
        SELECT
            d."Sale date"
            d."Amount ($)
        FROM data AS d
        ORDER BY "Sale date' ASC
    '''
    with sqlite3.connect('real_estate.db') as conn:
        database = pd.read_sql_query(query, conn)
    database["Amount ($)"] = pd.to_numeric(
        database["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )
    database = database.sort_values("Amount ($)")

    plt.(database["Sale date"], database["Amount ($)"], label="Real Estate Sales", color="navy")
    ax.tick_params(axis="x", labelrotation=90)
    fig.tight_layout(rect=[0, 0, 0.9, 1])
    ax.set_title("Sales in TTG 5091")
    ax.set_ylabel("Amount ($, in millions)")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    conn.close()



    return render_template('sales.html', img_base64=img_base64)

@app.route('/trends')
def trends():
    print("trends page")
    return render_template('trends.html')

@app.route('/predictions')
def predictions():
    print("predictions")
    return render_template('predictions.html')

if __name__== '__main__':
    app.run(debug=True, port=8000)