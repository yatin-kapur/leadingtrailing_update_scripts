import MySQLdb
import numpy as np
from sklearn import linear_model
from sklearn.cross_validation import cross_val_score

db = MySQLdb.connect(host='130.211.158.172',
                     user='root',
                     passwd='init.lambda',
                     db='leading_trailing')


def get_training_data(competition):
    cursor = db.cursor()
    query = """
            select lead_time_p90, trail_time_p90, gs, ga,
            top_four, top_six, relegation
            from competition_summary
            where competition <> '%s'
            order by competition desc, pos asc;
            """ % competition
    cursor.execute(query)
    data = cursor.fetchall()
    older = np.transpose(data)

    return older


def make_model(y, x, teams):
    model = linear_model.LogisticRegression()   # create model

    # cross validating the test model
    score = cross_val_score(model, x, y, cv=5)
    print(score)
    model.fit(x, y)
    probs = model.predict_proba(teams)
    probs = [x[1] for x in probs]

    return probs


def top_four(competition, teams):
    training = get_training_data(competition)
    y = training[4]    # target is topfour
    x = np.transpose(training[0:4])           # everything else is a feature

    probs = make_model(y, x, teams)
    return probs


def top_six(competition, teams):
    training = get_training_data(competition)
    y = training[5]    # target is topfour
    x = np.transpose(training[0:4])           # everything else is a feature

    probs = make_model(y, x, teams)
    return probs


def relegation(competition, teams):
    training = get_training_data(competition)
    y = training[6]    # target is topfour
    x = np.transpose(training[0:4])           # everything else is a feature


    probs = make_model(y, x, teams)
    return probs


# query = """
#         select lead_time_p90, trail_time_p90, gs, ga
#         from competition_summary
#         where competition = 'FA_Premier_League_2018-2019'
#         order by competition desc, pos asc;
#         """
# cursor = db.cursor()
# cursor.execute(query)
# data = cursor.fetchall()
# print(top_four('FA_Premier_League_2018-2019', data))
# print(top_six('FA_Premier_League_2018-2019', data))
# print(relegation('FA_Premier_League_2018-2019', data))
