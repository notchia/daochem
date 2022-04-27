import os
import numpy as np
import pandas as pd
import seaborn as sns
from pprint import pprint
from datetime import datetime


from utils.files import save_json, load_json
from daochem.database.analysis.base import RESULTS_DIR
from daochem.database.models.daos import Dao, DaoSurveyResponse, SURVEY_QUESTIONS

RESULTS_FILE = os.path.join(RESULTS_DIR, 'sentiment.json')
LOCAL_CSV = os.path.join('tmp', 'sentiment.csv')

Q_COLS = ['q1', 'q2', 'q3', 'q4', 'q5']

FORCE = False

if not os.path.isfile(RESULTS_FILE) or FORCE:
    responses = DaoSurveyResponse.objects.all()
    df = pd.DataFrame(list(DaoSurveyResponse.objects.all().values(
        'timestamp', 'dao_name_clean', 'q1', 'q2', 'q3', 'q4', 'q5')
        ))

    df['sentiment'] = df.apply(lambda row: row[Q_COLS].mean(), axis=1) #(row['q1'] + row['q2'] + row['q3'] + row['q4'] + row['q5'])/5
    df.to_csv(LOCAL_CSV)

    stats_to_compute = ['mean', 'median', 'min', 'max']
    df_q = df[Q_COLS]
    dfs = {
        'mean': df_q.mean(axis=0),
        'median': df_q.median(axis=0),
        'min': df_q.min(axis=0),
        'max': df_q.max(axis=0),
    }

    stats = {
        'meta': {
            'total_response_count': len(df.index),
            'unique_contributor_count': df['timestamp'].nunique(),
            'unique_dao_count': df['dao_name_clean'].nunique()
        },
        'overall_sentiment': {
            'mean': f"{df['sentiment'].mean():.2f}",
            'median': f"{df['sentiment'].median():.2f}",
            'min': f"{df['sentiment'].min():.2f}",
            'max': f"{df['sentiment'].max():.2f}",
        },
        'per_question': {
            q: {stat: f"{dfs[stat][q]:.2f}" for stat in stats_to_compute} for q in Q_COLS
        },
        'survey_questions': SURVEY_QUESTIONS
    }

    # Generate some figures too!
    sns.histplot(df, bins=5)

    save_json(stats, RESULTS_FILE)
else:
    stats = load_json(RESULTS_FILE)
    df = pd.read_csv(LOCAL_CSV, index_col=0)