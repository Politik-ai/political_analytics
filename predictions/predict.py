import pickle
from array import array
import numpy as np
import pandas as pd

# load the model from disk
model = pickle.load(open('logistic_model.sav', 'rb'))
print(model)

df_data = pd.read_pickle('data.pkl')
# df_data = df.drop('response',1)
print(df_data.head)
# df.to_csv('df.csv')..
x = df_data.iloc[500:501]
print(x)

y = model.predict(x)
print(y)


