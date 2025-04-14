import pandas as pd
import numpy as np

df = pd.read_csv('champions.csv', delimiter=';')
champions = df.to_dict('records')
print(champions)