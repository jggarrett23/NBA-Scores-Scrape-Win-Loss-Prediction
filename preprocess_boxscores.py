
import pandas as pd
import numpy as np
import pickle
import os


parentDir = r'D:\sportsScrape'
dataDir = os.path.join(parentDir, r'data')

boxscores_file = os.path.join(dataDir, 'teamBoxscores_dict.pickle')

# Load boxscore data
nGames, team_boxscores_dict = pickle.load(open(boxscores_file, 'rb'))

# Loop through each team and concatenate their boxscore dataframes into one long one
# Boxscore dataframes columns are:
    # Player, MIN, FGM, FGA, FG%, 3PM, 3PA, FTM, FTA, FT%, OREB, DREB, REB, AST, STL, BLK, TO, PF, PTS, +/-
# Create column for team they played against and the outcome.