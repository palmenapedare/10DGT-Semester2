import matplotlib.pyplot as plt
import pandas as pd

data = {
    "Ad_Spend": [100, 200, 300, 400, 500, 600, 700],
    "Revenue": [1200, 1900, 2800, 3400, 4100, 5000, 5800],
    "New_Customers": [15, 28, 35, 42, 50, 55, 62],
}
df_marketing = pd.DataFrame(data)

# TODO 1: Initialize a 1-row, 2-column subplot with figsize=(12, 4.5)
fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2,figsize=(12, 4.5))

# TODO 2: On ax1, plot a scatter plot of Ad_Spend vs Revenue
ax1.scatter(df_marketing["Ad_Spend"], df_marketing["Revenue"], color="purple")
ax1.set_title("Ad Spend vs Revenue")
ax1.set_ylabel("Revenue ($)")
ax1.set_xlabel("Amount spent on ads ($)")

# TODO 3: On ax2, plot a line plot of Ad_Spend vs New_Customers
ax2.plot(df_marketing["Ad_Spend"], df_marketing["New_Customers"], color="darkgreen", marker="o")
ax2.set_title("Customer Acquisition Trend")
ax2.set_ylabel("Amount spend on ads ($)")
ax2.set_xlabel("New customers")

plt.tight_layout()
plt.show()
