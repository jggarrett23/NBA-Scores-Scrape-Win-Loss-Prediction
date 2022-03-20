import os.path
import pickle
import pandas as pd


parentDir = r'D:\sportsScrape'
dataDir = os.path.join(parentDir, r'data')

# Read in data
player_stats = pd.read_csv(os.path.join(dataDir, 'player_allgame_stats.csv'))

# Preprocess
player_stats = player_stats.rename(columns={player_stats.columns[2]: 'Vs', player_stats.columns[3]: 'Date'}).drop(
    columns=['+/-', 'Season'])

player_stats['Vs'] = player_stats.apply(
    lambda row: row['Vs'].replace(row['Team'], '').replace('vs. ', '').replace('@ ', ''),
    axis=1)

player_stats['W/L'] = player_stats.apply(lambda row: 1 if row['W/L'] == 'W' else 0, axis=1)

player_stats['Date'] = player_stats.Date.apply(lambda date: pd.to_datetime(date))

# remove duplicate rows
player_stats = player_stats.drop_duplicates()

teams = player_stats.Team.unique()

# number of games back to average over
nGames_back = 5
avg_stats_cols = ['Player', 'PTS', 'MIN', 'FG%', '3PM', '3P%', 'FT%', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']
player_stats_processed = {}
for iTeam in teams:
    team_df = player_stats[player_stats['Team'] == iTeam]
    team_df = team_df.sort_values(by='Date')
    game_dates = team_df.Date.unique()

    # use pandas rolling to compute moving average stats for each player
    # stats of interest: pts, fg%, 3PM, 3P%, FT%, REB, AST, STL, BLK, TOV, PF

    player_mvAvg_stats = team_df.loc[:, avg_stats_cols].groupby('Player').rolling(window=nGames_back,
                                                                                  min_periods=1).mean()

    mv_avg_colnames = ['{}_gamesBack_Avg{}'.format(nGames_back, col) for col in avg_stats_cols[1:]]

    player_mvAvg_stats = player_mvAvg_stats.reset_index(level=0).rename(
        columns=dict(zip(avg_stats_cols[1:], mv_avg_colnames)))

    team_df = team_df[['Team', 'Vs', 'Date']].merge(player_mvAvg_stats, how='outer', left_on=team_df.index, right_on=player_mvAvg_stats.index)

    # store processed stats in a dictionary
    player_stats_processed[iTeam] = team_df


pickle.dump(player_stats_processed, open(os.path.join(dataDir, 'processed_playerStats.pickle'), 'wb'))