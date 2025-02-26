# goekayyavuz

## import libaries
import requests
import pandas as pd
from bs4 import BeautifulSoup
import sqlite3

try:
    url = 'https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures'
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
except requests.exceptions.RequestException as e:
    print(f"Error while accessing website: {e}")
    exit()

tables = soup.find_all("table")

## find the right table class inside of all tables
for i, table in enumerate(tables):
    print(f"Tabelle {i}: {table.get('class')}")

table = soup.find("table", {"class": "stats_table"})
if not table:
    print("Table not found.")
    exit()

## parse all data inside of variables
if table:
    rows = table.find_all("tr")
    matches = []  # store the variables inside of this list
    for row in rows:
        cols = row.find_all("td")
        if cols:
            dayofweek = cols[0].text.strip()
            date = cols[1].text.strip()
            start_time = cols[2].text.strip()
            home_team = cols[3].text.strip()
            home_xg = cols[4].text.strip()
            score = cols[5].text.strip()
            away_xg = cols[6].text.strip()
            away_team = cols[7].text.strip()
            attendance = cols[8].text.strip()
            venue = cols[9].text.strip()
            referee = cols[10].text.strip()

            matches.append(
                [dayofweek, date, start_time, home_team, home_xg, score, away_xg, away_team, attendance, venue,
                 referee])

columns = ['dayofweek', 'date', 'start_time', 'home_team', 'home_xg', 'score', 'away_xg', 'away_team', 'attendance',
           'venue', 'referee']
df = pd.DataFrame(matches, columns=columns)  # create dataframe with matches list

## configure sql connection
conn = sqlite3.connect("premier_league.db")
cursor = conn.cursor()

## sql command to create the table
cursor.execute('''
CREATE TABLE IF NOT EXISTS matches_2425(
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               dayofweek TEXT,
               date TEXT,
               starttime TEXT,
               home_team TEXT,
               home_xg FLOAT,
               score TEXT,
               away_xg FLOAT,
               away_team TEXT,
               attendance INTEGER,
               venue TEXT,
               referee TEXT
                )


''')

## store the dataframe in sql database
df.to_sql("matches_2425", con=conn, if_exists="replace", index=False)
conn.close()

## test if the table is stored correctly
conn = sqlite3.connect("premier_league.db")
cursor = conn.cursor()
query = "SELECT * FROM matches_2425"
pd.read_sql(query, conn)


# Points Table
def home_score(x):
    score_list = x.split('–')
    #print(score_list[0])
    return score_list[0]

def away_score(x):
    score_list = x.split('–')
    return score_list[1]


# Taking Home Team Only
df_points_temp_home = pd.DataFrame()
df_points_temp_away = pd.DataFrame()
df_points_temp = pd.DataFrame()

df_points_temp_home['Team'] = df[df.score != ''].home_team

df_points_temp_home['Win'] = [1 if int(home_score(x)) > int(away_score(x)) else 0 for x in df[df.score != ''].score]
df_points_temp_home['Loss'] = [1 if int(home_score(x)) < int(away_score(x)) else 0 for x in df[df.score != ''].score]
df_points_temp_home['Draw'] = [1 if int(home_score(x)) == int(away_score(x)) else 0 for x in df[df.score != ''].score]
df_points_temp_home['GoalScored'] = [int(home_score(x)) for x in df[df.score != ''].score]
df_points_temp_home['GoalAgainst'] = [int(away_score(x)) for x in df[df.score != ''].score]
df_points_temp_home['GoalDifference'] = [int(home_score(x)) - int(away_score(x)) for x in df[df.score != ''].score]

# Taking Away Team Only
df_points_temp_away['Team'] = df[df.score != ''].away_team

df_points_temp_away['Win'] = [1 if int(home_score(x)) < int(away_score(x)) else 0 for x in df[df.score != ''].score]
df_points_temp_away['Loss'] = [1 if int(home_score(x)) > int(away_score(x)) else 0 for x in df[df.score != ''].score]
df_points_temp_away['Draw'] = [1 if int(home_score(x)) == int(away_score(x)) else 0 for x in df[df.score != ''].score]
df_points_temp_away['GoalScored'] = [int(away_score(x)) for x in df[df.score != ''].score]
df_points_temp_away['GoalAgainst'] = [int(home_score(x)) for x in df[df.score != ''].score]
df_points_temp_away['GoalDifference'] = [int(away_score(x)) - int(home_score(x)) for x in df[df.score != ''].score]

df_points_temp = pd.concat([df_points_temp_home, df_points_temp_away], ignore_index=True)


# Final Table

df_points = df_points_temp.groupby('Team').agg(
gamesplayed = ('Team','count'),
    win=('Win','sum'),
    draw=('Draw','sum'),
    loss=('Loss','sum'),
    goalscored=('GoalScored','sum'),
    goalagainst=('GoalAgainst','sum'),
    goaldifference=('GoalDifference','sum')
)

df_points['points'] = df_points['win']*3+df_points['draw']
df_points.sort_values(by='points',ascending=False, inplace=True)

print(df_points)