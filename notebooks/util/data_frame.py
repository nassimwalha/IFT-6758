import pandas as pd
import numpy as np
def get_data_frame (data):
    Empty_Net = []
    Game_ID = []
    Game_Type = []
    Event_ID = []
    Event_Type = []
    Power_Game = []
    Team_Attack = []
    Coordinate_X = []
    Coordinate_Y = []
    Period = []
    Period_Time = []
    Time = []
    Shooters = []
    Goalies = []
    Shoot_type = []
    Home = []
    Away = []
    Home_Rink = []

    for a in range(len(data.data)):
        for b in range(len(data.data[a]['data'])):
            for i in range(len(data.data[a]['data'][b]['liveData']['plays']['allPlays'])):
                if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'] == 'Shot' or \
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'] == 'Goal':
                    Game_ID.append(data.data[a]['data'][b]['gamePk'])
                    Game_Type.append(data.data[a]['data'][b]['gameData']['game']['type'])
                    Event_ID.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['eventIdx'])
                    Event_Type.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'])
                    Home.append(data.data[a]['data'][b]['gameData']['teams']['home']['name'])
                    Away.append(data.data[a]['data'][b]['gameData']['teams']['away']['name'])
                    if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['periodType'] == 'SHOOTOUT':
                        Home_Rink.append(np.nan)
                    else:
                        Home_Rink.append(data.data[a]['data'][b]['liveData']['linescore']['periods'][
                                             data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about'][
                                                 'period'] - 1]['home'].get('rinkSide', np.nan))

                    if 'strength' in data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result'].keys():
                        Power_Game.append(
                            data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['strength']['name'])
                    else:
                        Power_Game.append(np.nan)

                    if 'emptyNet' in data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result'].keys():
                        Empty_Net.append(
                            data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['emptyNet'])
                    else:
                        Empty_Net.append(np.nan)
                    Team_Attack.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['team']['name'])
                    Coordinate_X.append(
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['coordinates'].get('x', np.nan))
                    Coordinate_Y.append(
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['coordinates'].get('y', np.nan))
                    Period.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['period'])
                    Period_Time.append(
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['periodTime'])
                    Time.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['dateTime'])
                    Shoot_type.append(
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result'].get('secondaryType',
                                                                                                  np.nan))

                    for j in range(len(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'])):
                        if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j][
                            'playerType'] == 'Shooter':
                            Shooters.append(
                                data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['player'][
                                    'fullName'])
                        if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j][
                            'playerType'] == 'Scorer':
                            Shooters.append(
                                data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['player'][
                                    'fullName'])
                        if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j][
                            'playerType'] == 'Goalie':
                            Goalies.append(
                                data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['player'][
                                    'fullName'])

                if len(Goalies) < len(Game_ID):
                    Goalies.append(np.nan)

    data_game = {'Game_ID': Game_ID, 'Game_Type': Game_Type, 'Event_ID': Event_ID, 'Home_Team': Home,
                 'Home_Rink': Home_Rink, 'Away_Team': Away, 'Event_Type': Event_Type, 'Shoot_Type': Shoot_type,
                 'Time': Time, 'Period': Period, 'Period_Time': Period_Time, 'Team_Attack': Team_Attack,
                 'Power_Game': Power_Game, 'Empty_Net': Empty_Net, 'Shooters_scorer': Shooters, 'Goalies': Goalies,
                 'X_Coordinate': Coordinate_X, 'Y_Coordinate': Coordinate_Y}
    df = pd.DataFrame(data_game)
    return df


