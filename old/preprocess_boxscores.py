
import pandas as pd
import numpy as np
import pickle
import os


parentDir = r'D:\sportsScrape'
dataDir = os.path.join(parentDir, r'../data')

boxscores_file = os.path.join(dataDir, 'teamBoxscores_dict.pickle')

# Load each games individual boxscore data. Includes player stats
team_boxscores_dict = pickle.load(open(boxscores_file, 'rb'))

# Load dataframe of boxscores. Does not include player stats
all_gamesBoxscores_df = pd.read_csv(os.path.join(dataDir, 'all_gamesBoxscores_summary.csv'))

# Loop through each team and concatenate their boxscore dataframes into one long one
# Boxscore dataframes columns are:
    # Player, MIN, FGM, FGA, FG%, 3PM, 3PA, FTM, FTA, FT%, OREB, DREB, REB, AST, STL, BLK, TO, PF, PTS, +/-
# Create column for team they played against and the outcome.
player_allGame_stats = pd.DataFrame()
for team in team_boxscores_dict.keys():
    team_games = team_boxscores_dict[team]
    for game_date in team_games.keys():
        game_boxscoreDF = team_games[game_date]

        # use the general game summary df to get info about who the opponent was and who won the game
        overall_gameSummary = all_gamesBoxscores_df[all_gamesBoxscores_df['Date'].str.match(game_date) & all_gamesBoxscores_df['Team'].str.match(team)]

        # create column in the games boxscore df with player stats for the opposing team, game date, and w/l outcome
        game_boxscoreDF['W/L'] = overall_gameSummary['W/L'].values[0]
        game_boxscoreDF['Vs'] = overall_gameSummary['Vs'].values[0]
        game_boxscoreDF['Date'] = overall_gameSummary['Date'].values[0]

        player_allGame_stats.append(game_boxscoreDF)

player_allGame_stats.to_csv(os.path.join(dataDir, 'player_allgame_stats.csv'), index=False)



