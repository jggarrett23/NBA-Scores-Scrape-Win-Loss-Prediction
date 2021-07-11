#  TODO: Determine questions. E.g., predicting wins based off individual player points or which team would win given their players.

import pandas as pd
import numpy as np
import re
import bs4
from bs4 import BeautifulSoup as soup
import requests
import urllib3
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from collections import defaultdict
from sklearn.linear_model import LogisticRegression

import time
import os
from datetime import datetime, date

startTime = datetime.now()

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

# read in team names and abbreviations
nba_teams_dict = {}
with open('nba_teamNames.txt') as f:
    for line in f:
        (key, val) = line.split(',')
        nba_teams_dict[key] = val.strip()

browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')
browser.maximize_window()

playerSearch_url = 'https://www.nba.com/stats/players/traditional/?sort=OREB&dir=-1&Season=2020-21&SeasonType=Regular%20Season'
gameBoxscore_url = 'https://www.nba.com/stats/teams/boxscores/?Season=2020-21&SeasonType=Regular%20Season'

# Scrape Player Stats
#browser.get(playerSearch_url)

# click drop down to show all game stats
#browser.find_element_by_xpath('/html/body/main/div/div/div[2]/div/div/nba-stat-table/div[1]/div/div/select/option[1]').click()

#player_search_results = requests.get(browser.current_url)
#playerPage_html = browser.execute_script("return document.body.innerHTML")

#playerPage = soup(playerPage_html, "html.parser")

# Scrape Team Box Scores
browser.get(gameBoxscore_url)
browser.find_element_by_xpath('/html/body/main/div/div/div[2]/div/div/nba-stat-table/div[1]/div/div/select/option[1]').click()
boxscore_search_results = requests.get(browser.current_url)
boxscore_html = browser.execute_script('return document.body.innerHTML')

boxscore_page = soup(boxscore_html, 'html.parser')
boxscore_tableContainer = boxscore_page.find('div', {'class': 'nba-stat-table__overflow'})

game_container = boxscore_tableContainer.find('tbody')
game_container = game_container.findAll('tr')

parent_link = 'https://www.nba.com/'

team_boxscores_dict = defaultdict(dict)
# select even game number to avoid duplicates
for iGame in range(0, len(game_container), 2):
    game = game_container[iGame]
    g = game.select_one('td:nth-child(2)')
    game_date = game.select_one('td:nth-child(3)').text.strip()

    # get games boxscore
    browser.get(parent_link + game.select_one('td:nth-child(2)').find('a')['href'][7:])

    browser.execute_script("window.scrollTo(0,500)")

    browser.find_element_by_id('box-score').click()

    team_boxscores = browser.find_elements_by_tag_name('table')
    team_name_containers = browser.find_elements_by_class_name('p-4')
    for iTeam, bx_score in enumerate(team_boxscores):

        # first team_name_container is of final score, dont need
        team_name = team_name_containers[iTeam+1].find_element_by_tag_name('span').text

        team_nameAbv = nba_teams_dict[team_name]

        # have to select tables parent to read into pandas
        bx_parent = bx_score.find_element_by_xpath('..')
        bx_scoreDF = pd.read_html(bx_parent.get_attribute('innerHTML'))[0]

        team_boxscores_dict[team_nameAbv][game_date] = bx_scoreDF

browser.quit()






player_tableContainer = playerPage.find('div', {'class': 'nba-stat-table__overflow'})

player_df = pd.read_html(str(player_tableContainer))[0]

# columns of interest: player, team, age, pts (points),
# fg% (field goal %), 3P%, FT%, REB, AST, TOV (turn overs), STL (steals),
# BLK, PF
player_df = player_df[['PLAYER', 'TEAM', 'W', 'L', 'AGE', 'PTS', 'FG%',
                          '3P%', 'FT%', 'REB', 'AST', 'TOV', 'STL',
                          'BLK', 'PF']]



boxscore_df = pd.read_html(str(boxscore_tableContainer))[0]

boxscore_df.rename(columns={boxscore_df.columns[1]: 'Vs'}, inplace=True)

boxscore_df = boxscore_df[['Team', 'Vs', 'W/L', 'PTS', 'FG%',
                                   '3P%', 'FT%', 'REB', 'AST', 'STL', 'BLK', 'TOV']]
# clean up matchup column
boxscore_df['Vs'] = boxscore_df.apply(lambda row: row['Vs'].replace(row['Team'], '').replace('vs. ', '').replace('@ ', ''),
                      axis=1)

# Transform W/L column to binary outcome
boxscore_df['W/L'] = boxscore_df.apply(lambda row: 1 if row['W/L'] == 'W' else 0, axis = 1)

# Exploratory Analysis

# --- Team's Top 5 Scorers Predictive of W/L vs Other Team ---
n_players = 10
topN_teamScorers = player_df.sort_values(['PTS'], ascending=False).groupby('TEAM').head(n_players)

teams = topN_teamScorers['TEAM'].unique()

teams_avgPts = np.empty([len(boxscore_df), n_players*2])
for iGame in range(len(boxscore_df)):
    team1 = boxscore_df['Team'][iGame].strip()
    team2 = boxscore_df['Vs'][iGame].strip()

    team1_avgPts = topN_teamScorers[topN_teamScorers['TEAM'] == team1]['PTS'].values
    team2_avgPts = topN_teamScorers[topN_teamScorers['TEAM'] == team2]['PTS'].values

    teams_avgPts[iGame, :] = np.append(team1_avgPts, team2_avgPts, axis=0)

y = boxscore_df['W/L'].values

clf = LogisticRegression(random_state=0, penalty='l2', max_iter=200).fit(teams_avgPts, y)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(player_df.head())
    print(boxscore_df.head())
    print(f'Win Loss Classifier Accuracy: {round(clf.score(teams_avgPts, y) * 100,2)}%')
