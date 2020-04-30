import time
import re
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup

def work_player_profile(param, season):
    url = "https://www.basketball-reference.com" + param
    res = requests.get(url)
    soup = BeautifulSoup(res.text)

    data_dict = {}

    per_game = soup.find(attrs={'id': 'all_per_game'})
    for row in per_game.findAll("tr"):
        if 'id' in row.attrs and row.attrs['id'] == "per_game." + season:
            data_dict['fga'] = float(row.find('td', attrs={'data-stat': 'fga_per_g'}).text)
            data_dict['fg3a'] = float(row.find('td', attrs={'data-stat': 'fg3a_per_g'}).text)
            data_dict['fta'] = float(row.find('td', attrs={'data-stat': 'fta_per_g'}).text)
            break

    advanced_table = soup.find(attrs={'id': 'all_advanced'})
    for child in advanced_table.children:
        if "table_outer_container" in child:
            other_soup = BeautifulSoup(child)
            rows = other_soup.findAll("tr")
    for row in rows:
        if 'id' in row.attrs and row.attrs['id'] == "advanced." + season:
            data_dict.update(
                {
                    'per': float(row.find('td', attrs={'data-stat': 'per'}).text),
                    'ts_pct': float(row.find('td', attrs={'data-stat': 'ts_pct'}).text),
                    'usg_pct': float(row.find('td', attrs={'data-stat': 'usg_pct'}).text),
                    'bpm': float(row.find('td', attrs={'data-stat': 'bpm'}).text),
                    'season': str(int(season)-1) + "-" + season[-2:],
                }
            )
            return data_dict

def get_stats_of_voting(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text)
    item = soup.find(attrs={'class': 'stats_table'})
    rows = item.findAll("tr")

    season = url.split(".html")[0][-4:]

    print(f"Current season: {season}")

    players_stats = defaultdict(list)

    for index, row in enumerate(rows):

        print(f"\tCurrent index: {index} of {len(rows)}")
        header_cells = row.findAll("th")
        for header_cell in header_cells:
            if 'data-stat' in header_cell.attrs and header_cell['data-stat'] == 'ranker' and 'csk' in header_cell.attrs:
                rank = int(header_cell.getText())
        td_cells = row.findAll("td")
        if not td_cells:
            continue
        for cell in td_cells:
            if 'data-stat' not in cell.attrs:
                continue
            if cell['data-stat'] == 'age':
                continue
            if cell['data-stat'] == 'team_id':
                base = "https://www.basketball-reference.com"
                try:
                    link = cell.find("a")['href']
                except Exception:
                    players_stats['win_pct'].append(0.5)  # average
                    continue
                url = base + link
                time.sleep(1)
                soup = BeautifulSoup(requests.get(url).text)
                for item in soup.findAll("p"):
                    if "Record" in item.text:
                        record = re.findall("\d+\-\d+", item.text)[0]
                        splitted = record.split("-")
                        players_stats['win_pct'].append(float(splitted[0]) / (float(splitted[1]) + float(splitted[0])))
                        break
                continue
            if cell['data-stat'] == 'player':
                time.sleep(1)
                advanced_dict = work_player_profile(cell.find("a")['href'], season)
                for key in advanced_dict:
                    players_stats[key].append(advanced_dict[key])
                players_stats[cell['data-stat']].append(cell.getText())
            else:
                text = cell.getText() or "0"
                players_stats[cell['data-stat']].append(float(text))
    return players_stats

seasons = range(1981, 2020)

new_data = defaultdict(list)

for season in seasons:
    full_url = f"https://www.basketball-reference.com/awards/awards_{str(season)}.html"
    cur_season_dict = get_stats_of_voting(full_url)
    for key in cur_season_dict:
        new_data[key].extend(cur_season_dict[key])

data_frame = pd.DataFrame(new_data)
data_frame.to_csv("mvp_votings.csv")
