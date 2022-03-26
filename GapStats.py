#!/bin/python3

import requests # HTTP Lib to get data
import sys # Script arg lib
import json # json file lib
import gspread # Google Api Lib
import pandas as pd
import argparse
from oauth2client.service_account import ServiceAccountCredentials

# Google Vars
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('gaptest-342721-88a00ca5760a.json', scope)
client = gspread.authorize(creds)

# Options
parser = argparse.ArgumentParser(description="cool stuff")
parser.add_argument('-w', '--write', help='Write the data to sheets', action='store_true')
parser.add_argument('-g', '--game',type=str, help='Game id')
parser.add_argument('-i', '--info', help='Prints info in console', action='store_true')
parser.add_argument('-t', '--table', help='Display the Datatable', action='store_true')
options = parser.parse_args(sys.argv[1:])

# Global Vars
region = 'NA1'
apikey = ''
if options.game:
    gameID = options.game
else:
    gameID = ''
redID = 200
blueID = 100

with open('championIdKey.json') as f:
    champ_ids = json.load(f)

with open('itemIdKey.json') as f:
    item_ids = json.load(f)

def getChamp(champID: int):
    return champ_ids[str(champID)]

def getItem(itemID: int):
    return item_ids[str(itemID)]

def main():
    
    # Initial request
    # gameID = sys.argv[1]

    # Google Stuff
    sheet = client.open('StatsTEST')
    worksheet = sheet.get_worksheet(0)

    # Dataframe initialization
    # player_dataframe = pd.DataFrame
    all_player_data = []

    # Data request and assignment
    GameRequest = requests.get(f'https://americas.api.riotgames.com/lol/match/v5/matches/{region}_{gameID}?api_key={apikey}')
    GameData = GameRequest.json()
    print(str(GameRequest.status_code))

    # Error catching
    if GameRequest.status_code == 404:
        print("Match ID not found")
    if GameRequest.status_code == 403:
        print("Bad API key")
    if GameRequest.status_code == 400:
        print('Incorrect Format')
    if GameRequest.status_code == 429:
        print('Too many requests, try again later')


    ### Match Info ###
    basic_info = {}
    basic_info['Game Duration'] = GameData['info']['gameDuration']
    basic_info['Match ID'] = GameData['info']['gameId']
    basic_info['Version'] = GameData['info']['gameVersion']
    # print(basic_info)

    red_team_objectives = {}
    blue_team_objectives = {}
    
    red_team_bans = {}
    blue_team_bans = {}

    ### Team Data ###
    for team in GameData['info']['teams']:
        team_object = {}
        banlist = []

        for ban in team['bans']:
            banlist.append(getChamp(ban['championId']))

        team_object['Baron Kills'] = team['objectives']['baron']['kills']
        team_object['Rift Herald Kills'] = team['objectives']['riftHerald']['kills']
        team_object['Dragon Kills'] = team['objectives']['dragon']['kills']
        team_object['Tower Kills'] = team['objectives']['tower']['kills']
        team_object['Inhibitor Kills'] = team['objectives']['inhibitor']['kills']
        team_object['Champion Kills'] = team['objectives']['champion']['kills']

        if team['teamId'] == blueID:
            blue_team_objectives = team_object
            blue_team_bans = banlist
        elif team['teamId'] == redID:
            red_team_objectives = team_object
            red_team_bans = banlist
   
    ### Player Data ###
    for participant in GameData['info']['participants']:
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
        ## Items ##
        # itemlist = []
        # for item in range(0,7):
        #     itemlist.append(getItem(participant[f"item{item}"]))
        # player_data['Items'] = itemlist
        ## Runes ##
        if options.info:
            print(str(player_data) + '\n')

        all_player_data.append(player_data)

    player_dataframe = pd.DataFrame.from_dict(all_player_data)
    
    if options.write:
        worksheet.update([player_dataframe.columns.values.tolist()] + player_dataframe.values.tolist())

    # print(player_data)
    # print(all_player_data)
    # print(itemlist)
    if options.table:
        print(player_dataframe)
    # print(current_player)

    # print(red_team_bans)
    # print(blue_team_bans)
    # print(red_team_objectives)
    # print(blue_team_objectives)

    


if __name__ == '__main__':
    main()
