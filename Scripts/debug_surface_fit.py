# scripts/debug_surface_fit.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sra.power import fit_data_to_surface
import matplotlib.pyplot as plt



# Load your test data
df = pd.read_pickle("autoencoder_training/VorstellungNEW.pkl")  # or .xlsx with pd.read_excel()


df = df.rename(columns={
    "G_mod": "G_eff",
    "T_mod": "T_eff",
    "Pmpp": "Pmpp",
    "Isc": "Isc",
    "Voc": "Voc",
    "Vmp": "Vmp",
    "Imp": "Imp"
})

# Run fitting
p_mpp = 320  # example
p_gamma = -0.38  # example
num_modules = 6

adjusted_p_mpp, adjusted_p_gamma, df_with_pred = fit_data_to_surface(df, p_mpp, p_gamma, num_modules)

# Print results
print(f"Adjusted p_mpp: {adjusted_p_mpp:.2f} W")
print(f"Adjusted p_gamma: {adjusted_p_gamma:.4f} %/K")

# Plot predicted vs measured Pmpp
plt.scatter(df_with_pred["Pmpp"], df_with_pred["Predicted_Pmpp"], alpha=0.5)
plt.xlabel("Measured Pmpp")
plt.ylabel("Predicted Pmpp")
plt.title("Predicted vs Measured Power")
plt.plot([df_with_pred["Pmpp"].min(), df_with_pred["Pmpp"].max()],
         [df_with_pred["Pmpp"].min(), df_with_pred["Pmpp"].max()], 'r--')  # y=x line
plt.grid(True)
plt.show()
