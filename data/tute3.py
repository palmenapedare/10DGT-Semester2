import matplotlib.pyplot as plt
import pandas as pd

# 1. Dataset: Daily Store Operations
data = {
    "Day": [f"Day {i}" for i in range(1, 11)],
    "Visitors": [120, 250, 80, 310, 290, 150, 400, 380, 190, 220],
    "Transactions": [15, 35, 8, 45, 40, 18, 60, 52, 22, 28],
}
df = pd.DataFrame(data)

# TODO 1: Filter df for days where Visitors > 250
high_traffic = df[df["Visitors"] > 250]
print(high_traffic)
    
# TODO 2: Create a list of colors ("crimson" if visitor count > 250, else "slategray")
colors = ["crimson" if v > 250 else "slategray" for v in df["Visitors"]]
print(colors)

# TODO 3: Create a bar chart of Day vs Visitors using the color list
plt.bar(df["Day"], df["Visitors"], color=colors)

# TODO 4: Add a dashed target line at 250 visitors using plt.axhline()
plt.axhline(250, color="maroon", ls="dotted", label="Target: 250")

# Add labels and display plot
plt.title("Daily Visitors (High Traffic Highlighted)")
plt.ylabel("Visitor Count")
plt.xlabel("Days")
plt.tight_layout()
plt.show()
