from collections import Counter
from contextlib import closing
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
import statistics
from pathlib import Path
from flask import Flask, render_template, request
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import io
import base64
from distutils.log import debug
from flask import *
from werkzeug.utils import secure_filename

#DB Generator
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(Path(app.root_path) / "uploads")
data_path = Path(app.config["UPLOAD_FOLDER"]) / "data.csv"
if data_path.is_file():
    df = pd.read_csv(data_path)
    print(df)
    with sqlite3.connect("real_estate.db") as conn:
        df.to_sql(name="data", con=conn, if_exists="replace", index=False)

def getlinesofbestfit():
    conn = sqlite3.connect('real_estate.db')
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
    
    sale_dates = database["Sale date"]
    days_since_first_sale = (sale_dates - sale_dates.min()).dt.days
    a, b = np.polyfit(days_since_first_sale, database["Amount ($)"], 1)
    lineofbestfitsaledate = f"Sale price = ${a:,.2f} * days + ${b:,.2f}"

    query = '''SELECT d."Bedrooms", d."Amount ($)" from DATA as d ORDER BY "Bedrooms" ASC'''
    bedrooms = pd.read_sql_query(query, conn)
    bedrooms["Amount ($)"] = pd.to_numeric(
        bedrooms["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )
    a, b = np.polyfit(bedrooms["Bedrooms"], bedrooms["Amount ($)"], 1)
    lineofbestfitbedrooms = f"Sale price = ${a:,.2f} * bedrooms + ${b:,.2f}"

    query = '''SELECT d."Land Size (m^2)", d."Amount ($)" from DATA as d ORDER BY "Land Size (m^2)" ASC'''
    landsize = pd.read_sql_query(query, conn)
    landsize["Amount ($)"] = pd.to_numeric(
        landsize["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )
    a, b = np.polyfit(landsize["Land Size (m^2)"], landsize["Amount ($)"], 1)
    lineofbestfitlandsize = f"Sale price = ${a:,.2f} * land size + ${b:,.2f}"

    return lineofbestfitsaledate, lineofbestfitbedrooms, lineofbestfitlandsize

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
            d."Land Size (m^2)",
            d."Suburb"
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
    lineofbestfitsaledate = f"Sale price = ${a:,.2f} * days + ${b:,.2f}"
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
    lineofbestfitbedrooms = f"Sale price = ${a:,.2f} * bedrooms + ${b:,.2f}"
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
        lineofbestfitsaledate=lineofbestfitsaledate,
        bedrooms_cost_base64=bedrooms_cost_base64,
        lineofbestfitbedrooms=lineofbestfitbedrooms
    )

@app.route('/predictions', methods=['GET', 'POST'])
def predictions():
    land_size_input = request.form.get("landsize", "")
    bedrooms_input = request.form.get("bedrooms", "")
    postcode_input = request.form.get("postcode", "")
    sale_date_input = request.form.get("saledate", "")
    prediction = None
    error = None
    landsizenull = False
    bedroomsnull = False
    postcodenull = False
    saledatenull = False

    query = '''SELECT "Suburb" FROM data WHERE "Suburb" IS NOT NULL'''
    with closing(sqlite3.connect("real_estate.db")) as conn:
        suburbs = [str(row[0]) for row in conn.execute(query).fetchall()]
    if postcode_input == str(statistics.mode(suburbs)):
        correctpostcode = True
    else:
        correctpostcode = False

    if request.method == 'POST':
        landsizenull = not land_size_input
        bedroomsnull = not bedrooms_input
        postcodenull = not postcode_input
        saledatenull = not sale_date_input

        if not postcode_input.isdigit() or len(postcode_input) != 4:
            error = "Enter a 4-digit postcode."
        elif not land_size_input or not bedrooms_input or not sale_date_input:
            error = "Enter a sale date, number of bedrooms, and land size to get a prediction."
        else:
            try:
                land_size_value = float(land_size_input)
                bedrooms_value = float(bedrooms_input)
                selected_date = pd.to_datetime(sale_date_input, format="%Y-%m-%d")
            except ValueError:
                error = "Enter valid numeric values for bedrooms and land size, and a valid sale date."
            else:
                prediction = predictionscalc(
                    land_size_value,
                    bedrooms_value,
                    selected_date
                )

    return render_template(
        'predictions.html',
        landsize=land_size_input,
        bedrooms=bedrooms_input,
        postcode=postcode_input,
        saledate=sale_date_input,
        prediction=prediction,
        error=error,
        correctpostcode=correctpostcode,
        landsizenull=landsizenull,
        bedroomsnull=bedroomsnull,
        postcodenull=postcodenull,
        saledatenull=saledatenull,
    )

def predictionscalc(land_size_value, bedrooms_value, selected_date):
    query = '''
        SELECT "Sale date", "Bedrooms", "Land Size (m^2)", "Amount ($)"
        FROM data
    '''
    with sqlite3.connect('real_estate.db') as conn:
        sales = pd.read_sql_query(query, conn)

    sales["Sale date"] = pd.to_datetime(sales["Sale date"], format="%d-%m-%y")
    sales["Amount ($)"] = pd.to_numeric(
        sales["Amount ($)"].str.replace(r"[$,]", "", regex=True)
    )
    first_sale_date = sales["Sale date"].min()
    days_since_first_sale = (sales["Sale date"] - first_sale_date).dt.days
    days_to_predict = (selected_date - first_sale_date).days

    variables = np.column_stack((
        np.ones(len(sales)),
        days_since_first_sale,
        sales["Bedrooms"],
        sales["Land Size (m^2)"]
    ))

    intercept, date_coefficient, bedroom_coefficient, land_size_coefficient = np.linalg.lstsq(
        variables, sales["Amount ($)"], rcond=None
    )[0]

    return (
        intercept
        + date_coefficient * days_to_predict
        + bedroom_coefficient * bedrooms_value
        + land_size_coefficient * land_size_value
    )

@app.route('/data', methods=['GET', 'POST'])
def data():
    #INDIVIDUAL DATA ENTRY
    address_input = request.form.get("address", "").strip()
    land_size_input = request.form.get("landsize", "")
    house_price_input = request.form.get("houseamount", "")
    bedrooms_input = request.form.get("bedroomsamount", "")
    postcode_input = request.form.get("postcode", "")
    sale_date_input = request.form.get("saledate", "")
    error = None
    addressnull = not address_input
    landsizenull = not land_size_input
    houseamountnull = not house_price_input
    bedroomsamountnull = not bedrooms_input
    postcodenull = not postcode_input
    saledatenull = not sale_date_input

    if request.method == 'POST':
        if any((addressnull, landsizenull, houseamountnull, bedroomsamountnull, postcodenull, saledatenull)):
            error = "Complete all fields."
        elif not postcode_input.isdigit() or len(postcode_input) != 4:
            error = "Enter a 4-digit postcode."
        else:
            try:
                land_size_value = Decimal(land_size_input)
                house_price_value = Decimal(house_price_input)
                bedrooms_value = int(bedrooms_input)
                sale_date_input_obj = datetime.strptime(sale_date_input, "%Y-%m-%d")
            except (InvalidOperation, ValueError):
                error = "The inputs are invalid."
            else:
                if not land_size_value.is_finite() or not house_price_value.is_finite():
                    error = "The inputs are invalid."
                else:
                    new_sale_date = sale_date_input_obj.strftime("%d-%m-%y")
                    house_price_input = f"${house_price_value:,.0f}"
                    land_size_input = f"{land_size_value:,.2f}"
                    with data_path.open(mode='ab+') as f:
                        f.seek(0, 2)
                        if f.tell() > 0:
                            f.seek(-1, 2)
                            if f.read(1) != b'\n':
                                f.seek(0, 2)
                                f.write(b'\n')
                    with data_path.open(mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            address_input,
                            new_sale_date,
                            house_price_input,
                            bedrooms_value,
                            land_size_input,
                            postcode_input,
                        ])
                    query = '''INSERT INTO data
                    ("Address", "Sale date", "Amount ($)", "Bedrooms", "Land Size (m^2)", "Suburb")
                    VALUES (?, ?, ?, ?, ?, ?)'''
                    addedvalues = (
                        address_input,
                        new_sale_date,
                        house_price_input,
                        bedrooms_value,
                        land_size_input,
                        postcode_input,
                    )
                    with closing(sqlite3.connect('real_estate.db')) as conn:
                        conn.execute(query, addedvalues)
                        conn.commit()
                    return render_template('datasuccess.html', addedvalues=addedvalues)
        return error, 400

    return render_template('data.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = [
        uploaded_file
        for uploaded_file in request.files.getlist('files')
        if uploaded_file.filename
    ]
    if not uploaded_files:
        return render_template('data.html', upload_error="Please choose a CSV file."), 400

    files_to_save = []
    filenames = set()
    for uploaded_file in uploaded_files:
        filename = secure_filename(uploaded_file.filename)
        if not filename or Path(filename).suffix.lower() != '.csv':
            return render_template('data.html', upload_error="Please choose CSV files only."), 400
        if filename.casefold() == "data.csv":
            return render_template(
                'data.html',
                upload_error="Please use a different name; data.csv is the combined file.",
            ), 400
        if filename.casefold() in filenames:
            return render_template(
                'data.html',
                upload_error="Each selected file must have a unique filename.",
            ), 400
        filenames.add(filename.casefold())
        files_to_save.append((uploaded_file, filename))

    upload_folder = Path(app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    master_path = upload_folder / "data.csv"
    frames = [pd.read_csv(master_path)] if master_path.is_file() else []
    for uploaded_file, filename in files_to_save:
        uploaded_file.save(upload_folder / filename)
        frames.append(pd.read_csv(upload_folder / filename))

    df_combined = pd.concat(frames, ignore_index=True)
    df_combined.to_csv(master_path, index=False)

    return render_template(
        'data.html',
        upload_success=f"Uploaded and merged {', '.join(filename for _, filename in files_to_save)}.",
    )

@app.route('/datasuccess')
def datasuccess(addedvalues):
    return render_template('datasuccess.html', addedvalues=addedvalues)

if __name__== '__main__':
    app.run(debug=True)