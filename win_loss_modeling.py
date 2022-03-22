import pickle
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegressionCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import GradientBoostingClassifier
from typing import Iterable

# TODO: Problem: Multi-classification of winning team
#  Use LogisticModel, Ensemble Classifiers, and K Nearest Neighbors to classify the winning team

parentDir = r'D:\sportsScrape'
dataDir = os.path.join(parentDir, r'data')

nba_dataset = pickle.load(open(os.path.join(dataDir, 'nba_dataset.pickle'), 'rb'))

allGames_features = nba_dataset['allGames_features']
allGames_labels = nba_dataset['allGames_labels']
allGames_info = nba_dataset['allGames_info']
teams = nba_dataset['teams']
stat_labels = nba_dataset['stat_featureLabels']

teams = np.sort(teams)
teams_binarized = LabelBinarizer().fit(teams)

allGames_labels_dense = teams_binarized.transform(allGames_labels)

X_train, X_test, y_train, y_test = train_test_split(allGames_features, allGames_labels_dense,
                                                    test_size=0.3, shuffle=True, random_state=123)


# TODO: convert into class with methods fit and transform to use in sklearn pipeline

# Scale data according to stats for both teams (e.g., PTS should be scaled to pts from both team, not independent)
def custom_stats_scaler() -> np.array:

    for col_start in range(0, 35, 5):
        col_range1 = np.asarray([*range(col_start, col_start+5)])
        col_range2 = col_range1 + 35

        X_subset = np.hstack((X_train[:, col_range1], X_train[:, col_range2]))

        stat_min = np.min(X_subset)
        stat_max = np.max(X_subset)

        X_train[:, col_range1] = (X_train[:, col_range1] - stat_min) / (stat_max - stat_min)
        X_train[:, col_range2] = (X_train[:, col_range2] - stat_min) / (stat_max - stat_min)

    return X_train


foo = 0



