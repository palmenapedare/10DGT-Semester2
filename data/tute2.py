import matplotlib.pyplot as plt
import pandas as pd

# 1. Raw Dataset
data = {
    "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "Cups_Coffee": [3, 2, 4, 1, 5, 2, 1],
    "Hours_Sleep": [6.5, 7.0, 5.5, 8.0, 5.0, 9.0, 8.5],
}
df = pd.DataFrame(data)

# TODO 1: Add a "Caffeine_mg" column (assuming 95mg per cup)

df["Caffeine_mg"] = 95 * df["Cups_Coffee"]

# TODO 2: Create a bar chart of Day vs Hours_Sleep using plt.bar()

plt.bar(df["Day"], df["Hours_Sleep"], label="Hours sleep per day", color="green")
#plt.bar(df["Day"], df["Caffeine_mg"], label="Caffeine consumed per day", color="blue")

#res = plt.grouped_bar(data, group_spacing=1)
#for container in res.bar_data:
    #plt.bar_label(container, padding=3)

# TODO 3: Add title ("Weekly Sleep"), labels, and call plt.show()
plt.title("Weekly Sleep")
plt.xlabel("Day")
plt.ylabel("Amount in hours")
plt.show()