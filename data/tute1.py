import matplotlib.pyplot as plt #plot
import pandas as pd #process data

# 1. Pandas: Create a DataFrame
data = {
    "Month": ["Jan", "Feb", "Mar", "Apr", "May"],
    "Sales": [150, 200, 180, 220, 300],
    "Expenses": [90, 110, 95, 130, 160],
}
df = pd.DataFrame(data)

# 2. Pandas: Inspect & Manipulate
print(df.head(3))  # View first 3 rows
df["Profit"] = df["Sales"] - df["Expenses"]  # Add calculated column

# 3. Matplotlib: Visualization
plt.figure(figsize=(7, 4))
plt.plot(df["Month"], df["Sales"], marker="o", label="Sales", color="navy")
plt.plot(
    df["Month"],
    df["Profit"],
    marker="s",
    label="Profit",
    color="forestgreen",
    linestyle="--",
)

# 4. Styling
plt.title("Company Performance")
plt.xlabel("Month")
plt.ylabel("Amount ($)")
plt.legend()
plt.grid(True)

plt.show()