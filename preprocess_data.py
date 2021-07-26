import os.path

import pandas as pd

parentDir = r'D:\sportsScrape'
dataDir = os.path.join(parentDir, r'data')

player_stats = pd.read_csv(os.path.join(dataDir, 'player_allgame_stats.csv'))
