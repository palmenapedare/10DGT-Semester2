from datetime import datetime
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
def chart():
    return render_template('chart.html')

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
    conn = sqlite3.connect('real_estate.db')
    #table
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
    sales_rows = conn.execute(query).fetchall()
    addressquery = 'SELECT DISTINCT Address FROM data ORDER BY "Sale date" ASC'
    addresslist = conn.execute(addressquery)
    
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

    oldest_date = database["Sale date"].min().date()
    oldestdate = oldest_date.strftime("%d-%m-%y")
    timedelta = (datetime.today().date() - oldest_date).days

    conn.close()
    return render_template(
        'sales.html',
        database=sales_rows,
        address_base64=address_base64,
        sale_date_cost_base64=sale_date_cost_base64,
        timedelta=timedelta
    )

@app.route('/trends')
def trends():
    ## SUBURB OVERVIEW
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
    pricelist = [
        int(row["Amount ($)"].replace("$", "").replace(",", ""))
        for row in above_million
    ]
    landsizelist = [row["Land Size (m^2)"] for row in above_million]
    if above_million:
        millionmeancost =f"{sum(pricelist) / len(pricelist):,.2f}"
        millionmediancost = f"{statistics.median(pricelist):,.2f}"
        millionmeanland = f"{sum(landsizelist) / len(landsizelist):,.2f}"
        millionmedianland = f"{statistics.median(landsizelist):,.2f}"
    else:
        millionmeancost = millionmediancost = None
        millionmeanland = millionmedianland = None

    query = '''
        SELECT CAST(
            REPLACE(REPLACE(d."Amount ($)", '$', ''), ',', '')
            AS INTEGER
        )
        FROM data AS d
    '''
    pricelist = [row[0] for row in conn.execute(query).fetchall()]
    meancost = f"{sum(pricelist)/len(pricelist):,.2f}"
    mediancost = f"{statistics.median(pricelist):,.2f}"

    query = '''
        SELECT d."Land size (m^2)" AS INTEGER
        FROM data AS d
    '''
    landsizelist = [row[0] for row in conn.execute(query).fetchall()]
    meanland = f"{sum(landsizelist)/len(landsizelist):,.2f}"
    medianland = f"{statistics.median(landsizelist):,.2f}"

    ##TIME OVERVIEW
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
    date_ax.bar(database["Sale date"], database["Amount ($)"], label="Real Estate Sales", color="navy")
    date_ax.tick_params(axis="x", labelrotation=45)
    date_fig.tight_layout()
    date_ax.set_title("Sale Date vs Amount")
    date_ax.set_ylabel("Amount ($)")
    date_ax.set_xlabel("Sale date (x)")
        #line of best fit via numpy, has to be converted from database["Sale date"]
    sale_dates = database["Sale date"]
    days_since_first_sale = (sale_dates - sale_dates.min()).dt.days
    a, b = np.polyfit(days_since_first_sale, database["Amount ($)"], 1)
    lineofbestfit1 = f"Sale price = ${a:,.2f} * days + ${b:,.2f}"
    date_ax.plot(
        sale_dates,
        a * days_since_first_sale + b,
        color="darkred",
        label=f"Trend: y = {a:,.2f}x + {b:,.2f}",
    )
    date_ax.legend()
    
    saledate_buf = io.BytesIO()
    date_fig.savefig(saledate_buf, format="png", bbox_inches="tight")
    saledate_buf.seek(0)
    
    sale_date_cost_base64 = base64.b64encode(saledate_buf.getvalue()).decode("utf-8")

    oldest_date = database["Sale date"].min().date()
    oldestdate = oldest_date.strftime("%d-%m-%y")
    timedelta = (datetime.today().date() - oldest_date).days

    #HOUSE SPECIFICS
    query = '''SELECT d."Bedrooms", d."Amount ($)" from DATA as d ORDER BY "Bedrooms" ASC'''
    bedrooms = pd.read_sql_query(query, conn)
    bedrooms["Amount ($)"] = pd.to_numeric(
        bedrooms["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )

    bedrooms_fig = Figure()
    FigureCanvasAgg(bedrooms_fig)
    bedrooms_ax = bedrooms_fig.subplots()
    bedrooms_ax.bar(
        bedrooms["Bedrooms"],
        bedrooms["Amount ($)"],
        label="Real Estate Sales",
        color="lightblue",
    )
    bedrooms_fig.tight_layout()
    bedrooms_ax.set_title("Bedrooms vs Amount")
    bedrooms_ax.set_ylabel("Amount ($)")
    bedrooms_ax.set_xlabel("Bedrooms")
    a, b = np.polyfit(bedrooms["Bedrooms"], bedrooms["Amount ($)"], 1)
    bedrooms_ax.plot(
        bedrooms["Bedrooms"],
        a * bedrooms["Bedrooms"] + b,
        color="darkred",
        label="Trend",
    )
    lineofbestfit2 = f"Sale price = ${a:,.2f} * bedrooms + ${b:,.2f}"
    bedrooms_ax.legend()
        
    bedrooms_buf = io.BytesIO()
    bedrooms_fig.savefig(bedrooms_buf, format="png", bbox_inches="tight")
    bedrooms_buf.seek(0)
        
    bedrooms_cost_base64 = base64.b64encode(bedrooms_buf.getvalue()).decode("utf-8")

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
        meanland=meanland,
        millionmeancost=millionmeancost,
        millionmediancost=millionmediancost,
        millionmeanland=millionmeanland,
        millionmedianland=millionmedianland,
        saledate_img=sale_date_cost_base64,
        oldestdate=oldestdate,
        timedelta=timedelta,
        lineofbestfit1=lineofbestfit1,
        bedrooms_cost_base64=bedrooms_cost_base64,
        lineofbestfit2=lineofbestfit2
    )

@app.route('/predictions')
def predictions():
    print("predictions")
    return render_template('predictions.html')

if __name__== '__main__':
    app.run(debug=True, port=8000)