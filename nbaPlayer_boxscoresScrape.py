# TODO: Only grab new games when running script every n days

import pandas as pd
from selenium import webdriver
from tqdm import tqdm
import os

parentDir = r'D:\sportsScrape'
saveDir = os.path.join(parentDir, r'data')

browser = webdriver.Chrome('C:\Program Files (x86)\Google\Chrome\Application\chromedriver')
browser.maximize_window()

playerBoxscore_url = 'https://www.nba.com/stats/players/boxscores/?Season=2020-21&SeasonType=Regular%20Season'

browser.get(playerBoxscore_url)

nBoxscore_Pages = int(
    browser.find_element_by_xpath('/html/body/main/div/div/div[2]/div/div/nba-stat-table/div[1]/div/div').text.split(
        'of ')[1])


def scrape_playerStats() -> pd.DataFrame:
    player_allGame_stats = pd.DataFrame()
    for iPage in tqdm(range(2, nBoxscore_Pages + 2)):

        # load boxscore
        if iPage > 3:
            browser.find_element_by_xpath(
                f'/html/body/main/div/div/div[2]/div/div/nba-stat-table/div[1]/div/div/select/option[{iPage}]').click()

        # Scrape table
        table_parent = browser.find_element_by_xpath(
            '/html/body/main/div/div/div[2]/div/div/nba-stat-table/div[2]/div[1]')

        boxscoreDF = pd.read_html(table_parent.get_attribute('innerHTML'))[0]

        player_allGame_stats = player_allGame_stats.append(boxscoreDF)

    player_allGame_stats.to_csv(os.path.join(saveDir, 'player_allgame_stats.csv'), index=False)

    return player_allGame_stats


if __name__ == '__main__':
    player_allGame_stats = scrape_playerStats()
    print(player_allGame_stats.head())
