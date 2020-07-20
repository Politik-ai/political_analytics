import featuretools as ft
import pandas as pd


es = ft.EntitySet(id="data")

#df = pd.read_pickle('data.pkl')
df = pd.read_csv('df.csv')

es = es.entity_from_dataframe(entity_id="congress",
                              dataframe=df,
                             # index="transaction_id",
                             # time_index="transaction_time",
                             )

print(es)