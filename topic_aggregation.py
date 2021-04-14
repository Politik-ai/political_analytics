import sys, os
sys.path.append(os.path.abspath('../data_collection/database_filler'))
from base import get_session
from framework import *
from sqlalchemy import func
import numpy as np
import yaml

db_location = sys.argv[1]
session = get_session(db_location)

bills = session.query(Bill)
max_id = session.query(func.max(Topic.id)).scalar()


adj_matrix = np.empty(shape=(max_id, max_id)).astype(int)
total_references = np.empty(shape=(max_id, 2))

num_bills = bills.count()
for i, b in enumerate(bills):
    print(f'{i}/{num_bills}')

    for t in [t for t in b.topics]:
        total_references[t.id, 0] = int(t.id)
        total_references[t.id, 1] += 1
        for t_2 in [t_2 for t_2 in b.topics if t_2 != t]:
            adj_matrix[t.id, t_2.id] += 1
            adj_matrix[t_2.id, t.id] += 1

sorted_total = total_references[total_references[:,1].argsort()]

topic_mapping = {}
for t in range(max_id):
    topic_mapping[t] = t

aggregate_count = 50
#Loop through topics, and add move adjacency connections to topics with highest related connection
for t, count in sorted_total[:-aggregate_count, :]:

    #get best adjacency index
    adj_row = adj_matrix[int(t),:]

    best_adj = int(np.argmax(adj_matrix[int(t),:], axis=0))
    adj_matrix[best_adj,:] += adj_matrix[int(t),:] 
    adj_matrix[int(t),:] = np.empty(shape=(1, max_id))

    #Update topic mapping for immediate topic to be removed, and all potential dependents
    topic_mapping[t] = best_adj
    for from_id, to_id in topic_mapping.items():
        if to_id != best_adj:
            continue
        topic_mapping[from_id] = best_adj

adj_matrix = adj_matrix.astype(int)

with open('results/topic_agg_mapping.yaml', 'w') as outfile:
    yaml.dump(topic_mapping, outfile, default_flow_style=False)

np.savetxt("results/topic_adjmatrix.csv", adj_matrix, delimiter=",")

