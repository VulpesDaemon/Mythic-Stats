#!/bin/python3

import requests # HTTP Lib to get data
import sys # Script arg lib
import json # json file lib
import gspread # Google Api Lib
import pandas as pd # Datatables for spreadsheets
import argparse # Options for console script
import time # Converting game duration
from oauth2client.service_account import ServiceAccountCredentials # Google Creds

# Google Vars
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('gaptest-342721-88a00ca5760a.json', scope)
client = gspread.authorize(creds)

# Options
parser = argparse.ArgumentParser(description="Required: -g -r -b -k -s")
parser.add_argument('-w', '--write', help='Write the data to sheets', action='store_true')
parser.add_argument('-g', '--game', type=str, help='Game id')
parser.add_argument('-i', '--info', help='Prints info in console', action='store_true')
parser.add_argument('-d', '--datatable', help='Display the Datatable', action='store_true')
parser.add_argument('-r', '--redteam', type=str, help='The team name on red side no spaces')
parser.add_argument('-b', '--blueteam', type=str, help='The team on blue side no spaces')
parser.add_argument('-k', '--week', type=int, help='The week of the game for writing to the spreadsheet')
parser.add_argument('-s', '--sheet', type=str, help='Which sheet you are writing to d or s')
options = parser.parse_args(sys.argv[1:])

#Riot API Vars
region = 'NA1'
apikey = 'RGAPI-6fc2b3f2-acfe-4ffd-86d4-d86956ddee42'
gameID = options.game
redID = 200
blueID = 100

# ID Jsons
with open('championIdKey.json') as f:
    champ_ids = json.load(f)

# Functions #
def convertTime(duration):
    return time.strftime('%M:%S', time.gmtime(duration))

def getChamp(champID: int):
    return champ_ids[str(champID)]

def getData(gameregion, gameid, apikey):
    GameRequest = requests.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{gameregion}_{gameID}?api_key={apikey}')
    GameData = GameRequest.json()
    print(str(GameRequest.status_code))
    if GameRequest.status_code == 404:
        print("Match ID not found")
    if GameRequest.status_code == 403:
        print("Bad API key")
    if GameRequest.status_code == 400:
        print('Incorrect Format')
    if GameRequest.status_code == 429:
        print('Too many requests, try again later')
    return GameData

# Code #
def main():
    week = options.week
    red_team_name = options.redteam
    blue_team_name = options.blueteam
    if options.sheet.lower() == 'd':
        sheet_name = 'Mythic Esports Dreamshatter Stats'
    if options.sheet.lower() == 's':
        sheet_name = 'Mythic Esports Stridebreaker Stats'
    sheet = client.open('Mythic Esports Stridebreaker Stats')
    worksheet = sheet.worksheet(f'Week {week}')
    all_player_data = []

    GameStatsjs = getData(region, gameID, apikey)

    ### Match Info ###
    basic_info = {}
    game_info = {}
    basic_info['Game Duration'] = convertTime(GameStatsjs['info']['gameDuration'])
    basic_info['Match ID'] = GameStatsjs['info']['gameId']
    basic_info['Version'] = GameStatsjs['info']['gameVersion'][0:4]
    game_info['Game Info'] = basic_info
    game_info_df = pd.DataFrame.from_dict(game_info, orient='index')

    for participant in GameStatsjs['info']['participants']:
        player_data = {}
        player_data['Player'] = participant['summonerName']
        player_data['Role'] = participant['teamPosition']
        if participant['teamPosition'] == "UTILITY": # renaming utility to support
            player_data['Role'] = 'SUPPORT'
        player_data['Champion'] = participant['championName']
        # assigning team for player
        if participant['teamId'] == blueID:
            player_data['Team'] = 'Blue'
        elif participant['teamId'] == redID:
            player_data['Team'] = 'Red'
        else:
            player_data['Team'] = 'N/A'
        player_data['Playtime'] = convertTime(participant['timePlayed'])

        ### Player Stats ###
        ## Basic Stats ##
        player_data['Kills'] = participant['kills']
        player_data['Deaths'] = participant['deaths']
        player_data['Assists'] = participant['assists']
        ## Specific Stats ##
        # Damage #
        player_data['Champion Damage'] = participant['totalDamageDealtToChampions']
        player_data['Structure Damage'] = participant['damageDealtToBuildings']
        # Taken and Healed #
        player_data['Damage Healed'] = participant['totalHeal']
        player_data['Damage Shielded'] = participant['totalDamageShieldedOnTeammates']
        player_data['Damage Taken'] = participant['totalDamageTaken']
        player_data['Damage Mitigated'] = participant['damageSelfMitigated']
        # Vision #
        player_data['Vision Score'] = participant['visionScore']
        player_data['Pinks Purchased'] = participant['visionWardsBoughtInGame']
        player_data['Wards Placed'] = participant['wardsPlaced']
        player_data['Wards Destroyed'] = participant['wardsKilled']
        # Gold and Exp #
        player_data['Gold Earned'] = participant['goldEarned']
        player_data['Champion Level'] = participant['champLevel']
        player_data['CS'] = participant['totalMinionsKilled'] + participant['neutralMinionsKilled']
        player_data['Minion Kills'] = participant['totalMinionsKilled']
        player_data['Jungle Minion Kills'] = participant['neutralMinionsKilled']
        ## Fun Stats ##
        player_data['Towers Destroyed'] = participant['turretKills']
        player_data['Inhibitors Destroyed'] = participant['inhibitorKills']
        player_data['CC Score'] = participant['timeCCingOthers']
        player_data['Damage per Minute'] = round(participant['challenges']['damagePerMinute'], 2)
        player_data['Gold per Minute'] = round(participant['challenges']['goldPerMinute'], 2)
        player_data['Vision per Minute'] = round(participant['challenges']['visionScorePerMinute'], 2)
        player_data['Winner'] = participant['win']
        player_data['Effective Healing And Shielding'] = participant['challenges']['effectiveHealAndShielding']
        player_data['Epic Monster Steals'] = participant['challenges']['epicMonsterSteals']
        player_data['Flawless Aces'] = participant['challenges']['flawlessAces']
        player_data['Aces'] = participant['challenges']['fullTeamTakedown']
        player_data['Multikills'] = participant['challenges']['multikills']
        player_data['Solo Kills'] = participant['challenges']['soloKills']    

        if options.info:
            print(str(player_data) + '\n')
        # Dataframe Init
        all_player_data.append(player_data)
        player_dataframe = pd.DataFrame.from_dict(all_player_data)
        
    if options.write:
        # worksheet.append_row([' '])
        worksheet.append_row([f'{blue_team_name} Vs. {red_team_name}'])
        worksheet.append_rows([game_info_df.columns.values.tolist()] + game_info_df.values.tolist())
        worksheet.append_rows([player_dataframe.columns.values.tolist()] + player_dataframe.values.tolist())

    if options.datatable:
        print(player_dataframe)


if __name__ == '__main__':
    main()
