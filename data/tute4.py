import matplotlib.pyplot as plt
import pandas as pd

# 1. Dataset: Sales Transactions
sales_data = {
    "Category": [
        "Tech",
        "Tech",
        "Apparel",
        "Apparel",
        "Tech",
        "Home",
        "Home",
        "Apparel",
    ],
    "Product": ["Phone", "Tab", "Shirt", "Jeans", "Watch", "Lamp", "Desk", "Hat"],
    "Revenue": [800, 450, 60, 90, 300, 450, 350, 25],
}
df_sales = pd.DataFrame(sales_data)
print(df_sales)

# TODO 1: Group by 'Category', sum the 'Revenue', and call .reset_index()
cat_summary = df_sales.groupby('Category')['Revenue'].sum().reset_index()
print(cat_summary)

# TODO 2: Create a bar chart using cat_summary['Category'] and cat_summary['Revenue']
plt.bar(cat_summary["Category"], cat_summary["Revenue"], color=["teal", "goldenrod", "coral"])

# TODO 3: Add title ("Total Revenue by Category"), y-label ("Revenue ($)"), 
plt.title("Total Revenue by Category")
plt.ylabel("Revenue ($)")
plt.xlabel("Category")
plt.show()