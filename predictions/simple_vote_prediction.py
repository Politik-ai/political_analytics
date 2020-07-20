#!/usr/bin/env python3
import sys, os
sys.path.append('../')
sys.path.append('../../data_collection/database_filler')
from data_collection.database_filler.framework import *
import pandas as pd
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from political_analytics.political_queries import *
sys.path.append(os.path.abspath('../../data_collection/database_filler'))
engine = create_engine('sqlite:///' + os.path.abspath('../../data_collection/political_db.db'), echo=False)
Session = sessionmaker(bind=engine)
import pickle

#What columns do we want 
"""
Each bill_state_vote basically:

Add boolean column for each topic?
Add boolean column for each sponsor? (add sponsor type?)
#Dummy variables

The 'y' variable is vote response. (trying to predict that)

Bill_State, Vote, Vote_Politician, Bill_Topic, Topic, Sponsorship
"""
from datetime import datetime, date

session = Session()
#This polid is just for testing
sponsors = get_all_politicians(session)
test_date = date(2014,3,3)
subset = filter_pols_by_date(session, sponsors, test_date)
sponsors = subset

polid_ids = [s.id for s in sponsors]

print(polid_ids)

scores = []

for polid in polid_ids[0:1]:
    print(f'Polid: {polid}')
    predictive_data = session.query(
        Bill_State, Vote_Politician
    ).join(
        Bill, Bill.id == Bill_State.bill_id
    ).join(
        Vote, Vote.bill_state_id == Bill_State.id
    ).join(
        Vote_Politician, Vote_Politician.vote_id == Vote.id
    ).filter(
            Vote_Politician.polid == polid
    # ).filter(
    #     or_(Vote_Politician.response == 0, Vote_Politician.response == 1)
    ).join(
        Sponsorship
    ).filter(
        Sponsorship.sponsor_type == 'primary'
    ).yield_per(10000)

    df = pd.read_sql(predictive_data.statement, session.bind)

    if df.shape[0] < 100:
        print('too little data, skipping')
        continue

    print('Got dataframe')
    # for response in df['response']:
    #     if response == -2:
    #         print('found 2')
    #     #print(type(response))
    #     print(response)


    sponsor_id_dict = {}
    topic_dict = {}
    i = 0
    num_bills = len(df['bill_id'])
    for bill_id in df['bill_id']:
        print(f'getting {i}/{num_bills} topic/sponsors')
        i += 1 
        s = get_sponsor_from_bill_id(session, bill_id)
        sponsor_id_dict[bill_id] = set([s.id for s in s.all()])
        
        t = get_topics_from_bill_id(session, bill_id)
        topic_dict[bill_id] = set([t.id for t in t.all()])

    print('got topic_dicts')


    #Convert to categorical:
    to_convert = ['bill_type', 'status_code']
    dummies = []
    for d in to_convert:
        dummy = pd.get_dummies(df[d])
        df = df.merge(dummy, left_index=True, right_index=True)
        del df[d]
    #Drop unnecesssary data
    del df['bill_state_identifier']
    del df['text_location']
    del df['short_title']
    del df['official_title']
    del df['vote_id']
    del df['id']

    dates = []
    for intro_date in df['intro_date']:
        dates.append(int(intro_date.strftime('%Y%m%d')))
    df['intro_date'] = dates
    #print(df.head())

    print('got dates')

    #add topic columns to dataframe
    topics = get_all_topics(session)
    t_found = 0
    for t in topics:
        to_skip = True
        bill_state_topic_list = []
        for bill_id in df['bill_id']:
            if t.id in topic_dict[bill_id]:
                print(f"T: {t_found}")
                t_found +=1
                to_skip = False
                bill_state_topic_list.append(1)
            else:
                bill_state_topic_list.append(0)
        if not to_skip:
            df[t.name] = bill_state_topic_list

    print('got topics')

    #Add sponsor columns to dataframe
    sponsors = get_all_politicians(session)
    test_date = date(2014,3,3)
    subset = filter_pols_by_date(session, sponsors, test_date)
    sponsors = subset
    s_found = 0
    for s in sponsors:
        to_skip = True
        bill_state_topic_list = []
        for bill_id in df['bill_id']:
            if s.id in sponsor_id_dict[bill_id]:
                #print(f"S: {s_found}")
                s_found += 1
                bill_state_topic_list.append(1)
                to_skip = False
            else:
                bill_state_topic_list.append(0)
        if not to_skip:
            df["Sponsor: " + str(s.id)] = bill_state_topic_list

    print('got sponsors')

    #With the sponsors and topics added, now separate the data into train/test/validate
    from sklearn.model_selection import train_test_split

    #Split data into train and test subsets
    test_split_ratio = 0.8
    response_df = df['response']
    response_df.head()
    df_data = df.drop('response',1)
    del df['bill_id']

    df.to_pickle('data.pkl')

    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(df_data, response_df, test_size=test_split_ratio, shuffle = True)
    X_train.head()


    #Run Regressions
    X = X_train[list(X_train)]
    Y = y_train
    from sklearn.linear_model import LinearRegression, LogisticRegression

    # #Without interaction Variables
    # # linear_model = LinearRegression().fit(X, Y)
    # # print('finished linear model')
    # # print("Model score:")
    # # print(linear_model.score(X_test,y_test))

    logistic_model = LogisticRegression().fit(X, Y)
    print('Logistic Model:')
    score = logistic_model.score(X_test, y_test)
    print(score)
    scores.append(score)

    print("saving model")
    filename = 'logistic_model.sav'
    pickle.dump(logistic_model, open(filename, 'wb'))






    # #In order to remove the increased variable complexity of adding interaction terms to a linear model, consider
    # #A Ridge Regression
    # from sklearn.linear_model import Ridge
    # ridge_reg = Ridge(alpha=1.0)
    # ridge_model = ridge_reg.fit(X_train,y_train)
    # print("Ridge model score:")
    # print(ridge_model.score(X_test,y_test))
    #
    #
    # #Lasso Regression
    # from sklearn.linear_model import Lasso
    # lasso_reg = Lasso(alpha=1.0)
    # lasso_model = lasso_reg.fit(X_train,y_train)
    # print("Lasso model score:")
    # print(lasso_model.score(X_test,y_test))


    # #PLS Regression
    # from sklearn.cross_decomposition import PLSRegression
    # pls = PLSRegression(n_components=2)
    # pls_reg = pls.fit(X_train,y_train)
    # print(f"Score: {pls_reg.score(X_test,y_test)}")

print("Average score:")
print(sum(scores)/len(scores))