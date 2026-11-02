from decimal import Decimal
import re
import statistics
from flask import Flask, render_template
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
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
               d."Amount ($)"
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

    address_buf = io.BytesIO()
    fig.savefig(address_buf, format="png", bbox_inches="tight")
    address_buf.seek(0)

    address_base64 = base64.b64encode(address_buf.read()).decode("utf-8")

    conn.close()

    #graph 2, Sale date v Cost
    query = '''
        SELECT
            d."Sale date",
            d."Amount ($)"
        FROM data AS d
        ORDER BY "Sale date" ASC
    '''
    with sqlite3.connect('real_estate.db') as conn:
        database = pd.read_sql_query(query, conn)
    database["Amount ($)"] = pd.to_numeric(
        database["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )
    database["Sale date"] = pd.to_datetime(database["Sale date"], format="%d-%m-%y")
    database = database.sort_values("Sale date")

    date_fig = Figure()
    FigureCanvasAgg(date_fig)
    date_ax = date_fig.subplots()
    date_ax.plot(database["Sale date"], database["Amount ($)"], label="Real Estate Sales", color="navy")
    date_ax.tick_params(axis="x", labelrotation=45)
    date_fig.tight_layout()
    date_ax.set_title("Sale Date vs Amount")
    date_ax.set_ylabel("Amount ($)")
    #line of best fit via numpy, has to be converted from database["Sale date"]
    sale_dates = mdates.date2num(database["Sale date"])
    a, b = np.polyfit(sale_dates, database["Amount ($)"], 1)
    date_ax.plot(database["Sale date"], a * sale_dates + b, color="darkred", label="Trend")

    saledate_buf = io.BytesIO()
    date_fig.savefig(saledate_buf, format="png", bbox_inches="tight")
    saledate_buf.seek(0)

    sale_date_cost_base64 = base64.b64encode(saledate_buf.getvalue()).decode("utf-8")

    conn.close()
    return render_template('sales.html', address_img=address_base64, saledate_img=sale_date_cost_base64)

@app.route('/trends')
def trends():
    conn = sqlite3.connect('real_estate.db')
    conn.row_factory = sqlite3.Row
    query = '''
        SELECT
            d."Address",
            d."Sale date",
            d."Amount ($)",
            d."Bedrooms",
            d."Land Size (m^2)",
            d."Suburb"
        FROM data AS d
        ORDER BY "Sale date" DESC
    '''
    database = conn.execute(query).fetchall()
    query = '''SELECT COUNT(*) FROM data AS d WHERE d."Suburb" = '5091' '''
    count5091 = conn.execute(query).fetchone()[0]

    query = '''
        SELECT
            d."Address",
            d."Sale date",
            d."Amount ($)",
            d."Bedrooms",
            d."Land Size (m^2)"
        FROM data AS d
        WHERE CAST(
            REPLACE(REPLACE(d."Amount ($)", '$', ''), ',', '')
            AS INTEGER
        ) > ?
        ORDER BY "Sale date" DESC
    '''
    above_million = conn.execute(query, (1_000_000,)).fetchall()
    count_above_million = len(above_million)

    query = '''
        SELECT CAST(
            REPLACE(REPLACE(d."Amount ($)", '$', ''), ',', '')
            AS INTEGER
        )
        FROM data AS d
    '''
    pricelist = [row[0] for row in conn.execute(query).fetchall()]
    meancost = sum(pricelist)/len(pricelist)
    mediancost = statistics.median(pricelist)

    query = '''
        SELECT d."Land size (m^2)" AS INTEGER
        FROM data AS d
    '''
    landsizelist = [row[0] for row in conn.execute(query).fetchall()]
    meanland = sum(landsizelist)/len(landsizelist)
    medianland = statistics.median(landsizelist)

    print("trends page")
    conn.close()
    return render_template(
        'trends.html',
        database=database,
        count5091=count5091,
        above_million=above_million,
        count_above_million=count_above_million,
        mediancost=mediancost,
        meancost=meancost,
        medianland=medianland,
        meanland=meanland
    )

@app.route('/predictions')
def predictions():
    print("predictions")
    return render_template('predictions.html')

if __name__== '__main__':
    app.run(debug=True, port=8000)