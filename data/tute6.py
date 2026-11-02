import matplotlib.pyplot as plt
import pandas as pd

products = {
    "Dept": [
        "Electronics",
        "Electronics",
        "Books",
        "Books",
        "Electronics",
        "Books",
    ],
    "Price": [120, 800, 15, 25, 150, 10],
    "Rating": [4.5, 4.8, 3.9, 4.2, 3.5, 4.7],
}
df_prod = pd.DataFrame(products)

# TODO 1: Filter df_prod for Rating >= 4.0
# high_rated_df = ...

# TODO 2: Group high_rated_df by 'Dept' and calculate the mean 'Price'
# dept_avg = ...

# TODO 3: Create a 1x2 subplot dashboard
# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

# TODO 4: Plot ax1 -> Bar chart of dept_avg['Dept'] vs dept_avg['Price']

# TODO 5: Plot ax2 -> Scatter plot of ALL products: df_prod['Price'] vs df_prod['Rating']

plt.tight_layout()
plt.show()
