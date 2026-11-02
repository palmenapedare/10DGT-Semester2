import matplotlib.pyplot as plt
import pandas as pd
import sqlite3

conn = sqlite3.connect('real_estate.db')
df = pd.read_csv("data.csv")
print(df)
query = '''
           SELECT
               d."Address",
               d."Sale date",
               d."Amount ($)",
               d."Bedrooms",
               d."Land Size (m^2)"
           FROM data AS d
           ORDER BY "Amount ($)" ASC
       '''

database = pd.read_sql_query(query, conn)
database["Amount ($)"] = pd.to_numeric(
    database["Amount ($)"].str.replace(r"[$,]", "", regex=True)
)
database = database.sort_values("Amount ($)")

plt.figure()
bars = plt.bar(database["Address"], database["Amount ($)"], label="Real Estate Sales", color="navy")
plt.xticks(rotation="vertical")
plt.tight_layout(rect=[0, 0, 0.9, 1]) 
plt.title("Sales in TTG 5091")

plt.show()
