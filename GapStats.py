#!/bin/python3

import requests # HTTP Lib to get data
import sys # Script arg lib
import json # json file lib
import gspread # Google Api Lib
import pandas as pd # Datatables for spreadsheets
import argparse # Options for console script
import time # Converting game duration
from oauth2client.service_account import ServiceAccountCredentials

# Google Vars
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('gaptest-342721-88a00ca5760a.json', scope)
client = gspread.authorize(creds)

# Options
parser = argparse.ArgumentParser(description="cool stuff")
parser.add_argument('-w', '--write', help='Write the data to sheets', action='store_true')
parser.add_argument('-g', '--game', type=str, help='Game id')
parser.add_argument('-i', '--info', help='Prints info in console', action='store_true')
parser.add_argument('-d', '--datatable', help='Display the Datatable', action='store_true')
parser.add_argument('-r', '--redteam', type=str, help='The team name on red side no spaces')
parser.add_argument('-b', '--blueteam', type=str, help='The team on blue side no spaces')
options = parser.parse_args(sys.argv[1:])

# Global Vars
region = 'NA1'
apikey = 'RGAPI-e10d8153-1a80-4a50-830f-0486e26f4186'
if options.game:
    gameID = options.game
else:
    gameID = '4264059993'
redID = 200
blueID = 100

with open('championIdKey.json') as f:
    champ_ids = json.load(f)

with open('itemIdKey.json') as f:
    item_ids = json.load(f)

def convertTime(duration):
    return time.strftime('%M:%S', time.gmtime(duration))

def getChamp(champID: int):
    return champ_ids[str(champID)]

def getItem(itemID: int):
    return item_ids[str(itemID)]

def main():

    # Team Stuff
    red_team_name = options.redteam
    blue_team_name = options.blueteam

    # Google Stuff
    sheet = client.open('GapPCLPlayoffs1')
    main_worksheet = sheet.worksheet('TEST')
    if options.blueteam:
        blue_worksheet = sheet.worksheet(blue_team_name)
    if options.redteam:
        red_worksheet = sheet.worksheet(red_team_name)

    # Dataframe initialization
    all_player_data = []
    blue_player_data = []
    red_player_data = []

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
    game_info = {}
    basic_info['Game Duration'] = convertTime(GameData['info']['gameDuration'])
    basic_info['Match ID'] = GameData['info']['gameId']
    basic_info['Version'] = GameData['info']['gameVersion'][0:4]
    game_info['Game Info'] = basic_info
    # print(basic_info)
    game_info_df = pd.DataFrame.from_dict(game_info, orient='index')
    print(game_info_df)

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
            blue_team_objectives['Objectives'] = team_object
            blue_team_bans['Bans'] = banlist
            # print(blue_team_objectives)
            # print(red_team_bans)
        elif team['teamId'] == redID:
            red_team_objectives['Objectives'] = team_object
            red_team_bans['Bans'] = banlist
            # print(red_team_objectives)
            # print(red_team_bans)

    # Creating team Dataframes
    if options.blueteam:
        blue_team_bansdf = pd.DataFrame.from_dict(blue_team_bans)
        blue_team_objectivesdf =  pd.DataFrame.from_dict(blue_team_objectives, orient='index')
        # blue_team_df = blue_team_bansdf + blue_team_objectivesdf
        # print(blue_team_df)
        # print(blue_team_bansdf)
        # print(blue_team_objectivesdf)

    if options.redteam:
        red_team_bansdf = pd.DataFrame.from_dict(red_team_bans)
        red_team_objectivesdf =  pd.DataFrame.from_dict(red_team_objectives, orient='index')
        # red_team_df = red_team_bansdf + blue_team_objectivesdf
        # print(red_team_df)
        # print(red_team_bansdf)
        # print(red_team_objectivesdf)
   
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
        ## Items ##
        # itemlist = []
        # for item in range(0,7):
        #     itemlist.append(getItem(participant[f"item{item}"]))
        # player_data['Items'] = itemlist
        ## Runes ##
        if options.info:
            print(str(player_data) + '\n')

        all_player_data.append(player_data)
        if player_data['Team'] == 'Blue' and options.blueteam:
            blue_player_data.append(player_data)
            blue_dataframe = pd.DataFrame.from_dict(blue_player_data)
        if player_data['Team'] == 'Red' and options.redteam:
            red_player_data.append(player_data)
            red_dataframe = pd.DataFrame.from_dict(red_player_data)


    player_dataframe = pd.DataFrame.from_dict(all_player_data)
    
    if options.write:
        if options.blueteam:
            # blue_worksheet.append_row([' '])
            blue_worksheet.append_row([f'Vs. {options.redteam}'])
            blue_worksheet.append_rows([game_info_df.columns.values.tolist()] + game_info_df.values.tolist())
            blue_worksheet.append_rows([blue_team_objectivesdf.columns.values.tolist()] + blue_team_objectivesdf.values.tolist())
            blue_worksheet.append_rows([blue_team_bansdf.columns.values.tolist()] + blue_team_bansdf.values.tolist())
            blue_worksheet.append_rows([blue_dataframe.columns.values.tolist()] + blue_dataframe.values.tolist())
        if options.redteam:
            # red_worksheet.append_row([' '])
            red_worksheet.append_row([f'Vs. {options.blueteam}'])
            red_worksheet.append_rows([game_info_df.columns.values.tolist()] + game_info_df.values.tolist())
            red_worksheet.append_rows([red_team_objectivesdf.columns.values.tolist()] + red_team_objectivesdf.values.tolist())
            red_worksheet.append_rows([red_team_bansdf.columns.values.tolist()] + red_team_bansdf.values.tolist())
            red_worksheet.append_rows([red_dataframe.columns.values.tolist()] + red_dataframe.values.tolist())
        else:
            main_worksheet.append_rows([player_dataframe.columns.values.tolist()] + player_dataframe.values.tolist())
            # main_worksheet.update([player_dataframe.columns.values.tolist()] + player_dataframe.values.tolist())

    # print(player_data)
    # print(all_player_data)
    # print(itemlist)
    if options.datatable:
        print(player_dataframe)
        print(blue_dataframe)
        print(red_dataframe)
    # print(current_player)

    # print(red_team_bans)
    # print(blue_team_bans)
    # print(red_team_objectives)
    # print(blue_team_objectives)

    


if __name__ == '__main__':
    main()
