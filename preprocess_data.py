import os.path
import pickle
import pandas as pd
from collections import namedtuple
import numpy as np
import re
from typing import Dict, Tuple


def extract_nGamesBack_playerStats(player_stats: pd.DataFrame, nGames_back: int) -> Tuple[pd.DataFrame, Dict]:
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

        team_df = team_df[['Team', 'Vs', 'Date']].merge(player_mvAvg_stats, how='outer', left_on=team_df.index,
                                                        right_on=player_mvAvg_stats.index)

        # store processed stats in a dictionary
        player_stats_processed[iTeam] = team_df

    return player_stats, player_stats_processed
    # pickle.dump(player_stats_processed, open(os.path.join(dataDir, 'processed_playerStats.pickle'), 'wb'))


def create_nba_dataset(player_stats: pd.DataFrame, player_stats_processed: Dict, topN_players: int) -> Dict:
    # Loop through each game and create a feature vector of team player stats
    allGames = player_stats[['Team', 'Vs', 'Date', 'W/L']].drop_duplicates()

    teams = player_stats.Team.unique()

    # Use even rows to avoid Home vs Away Away vs Home repeats
    allGames = allGames.iloc[range(0, len(allGames), 2),]

    # Use stats from top N players as features. Need to replace with lineups in the future

    # stats of interest
    stats_oi = ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF']

    allGames_info = list()
    allGames_features = np.empty([len(allGames), len(stats_oi) * topN_players * 2])
    allGames_labels = list()

    allGames = allGames.reset_index()

    # features are going to be the average stats of the top 5 players with the most minutes from each team
    for iRow, game in allGames.iterrows():
        home_team = game.Team.strip()
        away_team = game.Vs.strip()

        homeTeam_playerStats = player_stats_processed[home_team]
        awayTeam_playerStats = player_stats_processed[away_team]

        homeTeam_dates = np.unique(homeTeam_playerStats.Date)
        awayTeam_dates = np.unique(awayTeam_playerStats.Date)

        homeTeam_prevGame_idx = np.where(homeTeam_dates == game.Date)[0][0]
        awayTeam_prevGame_idx = np.where(awayTeam_dates == game.Date)[0][0]

        if homeTeam_prevGame_idx > 0:
            homeTeam_prevGame_date = homeTeam_dates[homeTeam_prevGame_idx - 1]
        else:
            homeTeam_prevGame_date = homeTeam_dates[homeTeam_prevGame_idx]

        if awayTeam_prevGame_idx > 0:
            awayTeam_prevGame_date = awayTeam_dates[awayTeam_prevGame_idx - 1]
        else:
            awayTeam_prevGame_date = awayTeam_dates[awayTeam_prevGame_idx]

        homePlayer_prevGameStats = homeTeam_playerStats[homeTeam_playerStats['Date'] == homeTeam_prevGame_date]
        awayPlayer_prevGameStats = awayTeam_playerStats[awayTeam_playerStats['Date'] == awayTeam_prevGame_date]

        homePlayer_prevGameStats = homePlayer_prevGameStats.sort_values(by='5_gamesBack_AvgMIN', ascending=False)
        awayPlayer_prevGameStats = awayPlayer_prevGameStats.sort_values(by='5_gamesBack_AvgMIN', ascending=False)

        stat_cols_idx = [i for i, x in enumerate(homePlayer_prevGameStats.columns) for stat in stats_oi if
                         re.search(stat, x)]
        playercol_idx = np.where(homePlayer_prevGameStats.columns == 'Player')[0][0]

        stat_cols_idx.insert(0, playercol_idx)

        home_topN_players = homePlayer_prevGameStats.iloc[:topN_players, stat_cols_idx]
        away_topN_players = awayPlayer_prevGameStats.iloc[:topN_players, stat_cols_idx]

        home_melt = home_topN_players.melt(id_vars='Player')
        away_melt = away_topN_players.melt(id_vars='Player')

        home_features = np.transpose(home_melt.value.to_numpy())
        away_features = np.transpose(away_melt.value.to_numpy())

        home_topN_playerNames = home_melt.Player.unique()
        away_topN_playerNames = away_melt.Player.unique()

        game_features = np.append(home_features, away_features)

        game_label = home_team if game['W/L'] else away_team

        game_info = namedtuple('game_info', ['HomeTeam', 'AwayTeam', 'Top{}_HomePlayers'.format(topN_players),
                                             'Top{}_AwayPlayers'.format(topN_players),
                                             'Date'])

        allGames_features[iRow] = game_features
        allGames_labels.append(game_label)
        allGames_info.append(game_info(home_team, away_team, home_topN_playerNames, away_topN_playerNames, game.Date))

    # conserve some memory
    allGames_features = allGames_features.astype('float32')

    allGames_info_dict = [info._asdict() for i, info in enumerate(allGames_info)]

    nba_dataset = {'allGames_features': allGames_features, 'stat_featureLabels': home_melt.variable.unique(), 'allGames_labels': allGames_labels,
                   'allGames_info': allGames_info_dict, 'teams': teams}

    return nba_dataset


if __name__ == '__main__':
    parentDir = r'D:\sportsScrape'
    dataDir = os.path.join(parentDir, r'data')

    # Read in data
    player_stats = pd.read_csv(os.path.join(dataDir, 'player_allgame_stats.csv'))

    player_stats, player_stats_processed = extract_nGamesBack_playerStats(player_stats, nGames_back=5)

    nba_dataset = create_nba_dataset(player_stats, player_stats_processed, topN_players=5)

    pickle.dump(nba_dataset, open(os.path.join(dataDir, 'nba_dataset.pickle'), 'wb'))
