import pandas as pd
import pickle
import numpy as np
import os

parentDir = r'D:\sportsScrape'
dataDir = os.path.join(parentDir, r'data')

# TODO: Move feature matrix creation into preprocess_data.py

# Load data
playerStats = pickle.load(open(os.path.join(dataDir, 'processed_playerStats.pickle'), 'rb'))
gameBoxscores = pd.read_csv(os.path.join(dataDir, 'all_gamesBoxscores_summary.csv'))

gameBoxscores['Date'] = gameBoxscores['Date'].apply(lambda x: pd.to_datetime(x))

# select only even games to avoid duplicates
away_points = gameBoxscores.loc[range(1, len(gameBoxscores), 2), 'PTS']

gameBoxscores = gameBoxscores.rename(columns={'PTS': 'HomePTs'})
gameBoxscores = gameBoxscores.iloc[range(0, len(gameBoxscores), 2),]
gameBoxscores['AwayPTs'] = away_points.to_numpy()

gameBoxscores = gameBoxscores.sort_values(by='Date')

# features are going to be the average stats of the top 5 players with the most minutes from each team
for iRow, game in gameBoxscores.iterrows():
    home_team = game.Team.strip()
    away_team = game.Vs.strip()

    homeTeam_playerStats = playerStats[home_team]
    awayTeam_playerStats = playerStats[away_team]

    homeTeam_dates = np.unique(homeTeam_playerStats.Date)
    awayTeam_dates = np.unique(awayTeam_playerStats.Date)

    homeTeam_prevGame_idx = np.where(homeTeam_dates == game.Date)[0][0]
    awayTeam_prevGame_idx = np.where(awayTeam_dates == game.Date)[0][0]

    if homeTeam_prevGame_idx > 0:
        homeTeam_prevGame_date = homeTeam_dates[homeTeam_prevGame_idx - 1]
    else:
        homeTeam_prevGame_date = homeTeam_dates[homeTeam_prevGame_idx]

    if awayTeam_prevGame_idx > 0:
        awayTeam_prevGame_date = homeTeam_dates[awayTeam_prevGame_idx - 1]
    else:
        awayTeam_prevGame_date = homeTeam_dates[awayTeam_prevGame_idx]

    homePlayer_prevGameStats = homeTeam_playerStats[homeTeam_playerStats['Date'] == homeTeam_prevGame_date]
    awayPlayer_prevGameStats = awayTeam_playerStats[awayTeam_playerStats['Date'] == awayTeam_prevGame_date]

    # TODO: put player stats into a matrix where each row is home team players and away team players
    # TODO: figure out best way to represent single player with multiple features.
    #  That way we can figure out which players are contributing the most to classifier accuracy.
    #  Or keep the player stats as separate features so we know what job they do that is most important
    #  Maybe have columns for stats for each top N players with most average minutes.
    #  Then columns for stats averaged across the rest of the players.
