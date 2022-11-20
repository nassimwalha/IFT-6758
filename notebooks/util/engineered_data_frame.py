import pandas as pd
import numpy as np
import math

def calculate_seconds(my_string):
    """
    Helper function to calculate  total number of seconds represented by a string in format
    mm:ss.
    """
    separated_time = my_string.split(":")
    return int(separated_time[0])*60+int(separated_time[1])

def transform_X(row):
    '''
    Given a row of the original data frame, this function transforms the coordinate X depending on the position of
    the teams in the rink. Since at the end the data is presented in a half-rink (we arbitrarily choose that
    this is the right half of the rink), when the attacking team plays on the right side of the rink , i.e
    the opponent's goal is on the left side, we need to flip the x coordinate.
    '''
    if str(row['Home_Rink']) == 'nan': #In case the rinkside information is not available, we assume the shot
        #is taken from the side that is the closest to the opponent's goal.
        return np.absolute(row['X_Coordinate'])

    else: #Otherwise we use rinkside information to determine whether to flip X coordinate as described above.
        if row['Home_Team'] == row['Team_Attack']:
            if row['Home_Rink'] == 'right':
                return -(row['X_Coordinate'])
            else:
                return row['X_Coordinate']
        else:
            if row['Home_Rink'] == 'left':
                return -(row['X_Coordinate'])
            else:
                return row['X_Coordinate']

def transform_last_X(row):
    '''
    Given a row of the original data frame, this function transforms the Last coordinate X depending on the position of
    the teams in the rink. Since we aim to present the data in a half-rink (we arbitrarily choose that
    this is the right half of the rink), when the attacking team plays on the right side of the rink , i.e
    the opponent's goal is on the left side, we need to flip the x coordinate.
    '''
    if str(row['Home_Rink']) == 'nan': #In case the rinkside information is not available, we assume the shot
        #is taken from the side that is the closest to the opponent's goal.
        return np.absolute(row['Last_Coordinate_X'])

    else: #Otherwise we use rinkside information to determine whether to flip X coordinate as described above.
        if row['Home_Team'] == row['Team_Attack']:
            if row['Home_Rink'] == 'right':
                return -(row['Last_Coordinate_X'])
            else:
                return row['Last_Coordinate_X']
        else:
            if row['Home_Rink'] == 'left':
                return -(row['Last_Coordinate_X'])
            else:
                return row['Last_Coordinate_X']

def get_distance(row):
    ''' Given a row of the original dataframe, this function computes the distance between one event and its preceding event'''
    return ((row['X_Coordinate']-row['Last_Coordinate_X'])**2+(row['Y_Coordinate']-row['Last_Coordinate_Y'])**2)**(1/2)

def get_angle(row):
    '''
    Given a row on the original dataframe, this function computes the angle of the shot. It first tests whether the last event was a Rebond. If false, it returns NAN. If true, it then tests whether the X_Transformed coordinate of the event is 89 (the x coordinate of the net). If also true, it returns an angle of either -90 or 90 degrees depending on its y coordinate. If false, it computes the angle according to the right triangle properties.
    '''
    if row['X_Transformed'] ==89:
        return 90*row['Y_Coordinate']/(np.abs(row['Y_Coordinate']))
    else :
        return np.arctan((row['Y_Coordinate']/(89-row['X_Transformed'])))*180/math.pi

def get_last_angle(row):
    '''
    Given a row on the original dataframe, this function computes the angle of the last shot. It first tests whether the last event was a Rebond. If false, it returns NAN. If true, it then tests whether the Last_X_Transformed coordinate of the event is 89 (the x coordinate of the net). If also true, it returns an angle of either -90 or 90 degrees depending on the last event's y coordinate. If false, it computes the angle of the last shot according to the right triangle properties.
    '''
    if row['Rebond']:
        if row['Last_X_Transformed'] ==89:
            return 90*row['Last_Coordinate_Y']/(np.abs(row['Last_Coordinate_Y']))
        else :
            return np.arctan((row['Last_Coordinate_Y']/(89-row['Last_X_Transformed'])))*180/math.pi
    else:
        return 0.0


def reset_penalty_stack():
    """
    Will be called on each period start to reset the penalty_stack to empty state.
    """
    penalty_stack = { #Dictionary contaning current penalty information. Will be updated in each event.
        "home": [], #List of current active penalites for the home team
        "away": [], #Same for away team. Format of penalty tuple: (playerID, penaltyMinutes, penaltySeverity, periodTime)
        "team_on_power_play": "none", #Current team that is on power play, can be "home", "away" or "none"
        "power_play_since": 0, #Period time of the start of the current powerplay, in seconds
    }
    return penalty_stack
#Penalty types compared from least severe to most severe
RANKED_PENALTIES = ["Minor", "Double Minor", "Major", "Misconduct", "Game Misconduct", "Match"]

def penalty_stack_update_on_any_event(penalty_stack,period_time):
    """
    Update function, will be the first one to be called on any event.
    Updates penalty_stack by deleting penalties which time is over.
    A penalty is represented as a tuple (player_id, penalty_minutes, penalty_severity, period_time).
    """
    #Preprocessing
    period_time = calculate_seconds(period_time)

    #Delete outdated penalties
    for team in ["home", "away"]:
        penalties_to_delete = []
        for i,penalty  in enumerate(penalty_stack[team]):
            penalty_duration = penalty[1]*60
            penalty_start = penalty[3]
            penalty_severity = penalty[2]
            if penalty_start+penalty_duration <= period_time:
                penalties_to_delete.append(penalty)
            elif penalty_severity == "Double Minor":
                #Double minors which have less than 2 mins left on the clock become minor penalties
                if period_time-penalty_start> 2*60:
                    new_minor_penalty = (penalty[0],2,"Minor", penalty_start+2*60)
                    penalty_stack[team][i]=new_minor_penalty
        for penalty in penalties_to_delete: #actually removing the penalties
            penalty_stack[team].remove(penalty)


    old_team_on_power_play = penalty_stack["team_on_power_play"]
    #Determining who's in powerplay now
    if len(penalty_stack["home"]) > len(penalty_stack["away"]): #In this case away is on powerplay
        penalty_stack["team_on_power_play"] = "away"
    elif len(penalty_stack["home"]) < len(penalty_stack["away"]):
        penalty_stack["team_on_power_play"] = "home"
    else:
        penalty_stack["team_on_power_play"] = "none"

    #Now if the team on power play changed, we set "power_play_since" to be perod_time, else we do nothing,
    #Thus preserving the start time of the already existing power_play
    if old_team_on_power_play != penalty_stack["team_on_power_play"]:
        if penalty_stack["team_on_power_play"] == "none":
            #Makes more sense to reset "power_play_since" to zero here, although can be set
            #to anything we want.
            penalty_stack["power_play_since"] = 0
        else :
            penalty_stack["power_play_since"] =  period_time

    return penalty_stack

def penalty_stack_update_on_penalty_event(penalty_stack, penalty_severity, penalty_minutes, period_time, player_id, team, home):
    """
    Update function to be called on each penalty event. Updates the penalty_stack.
    """
    #Pre-processing
    concerned_team = "home" if team==home else "away"

    if penalty_severity in ["Minor", "Bench Minor"]:
        if penalty_minutes==4:
            penalty_severity="Double Minor" #Creating Double Minor Severity for convenience.
        else:
            penalty_severity="Minor" #Bench Minor Penalties have same effect on the team as minor.
    if penalty_severity=="Match":
        penalty_minutes=5 #Match penalties are registered for 10 mins for statistical
        #Purposes but the team stays shorthanded for 5 minutes only. (Piazza question @95)

    period_time = calculate_seconds(period_time)

    if player_id in [penalty[0] for penalty in penalty_stack[concerned_team]] and penalty_severity!="Penalty Shot":
        #If player already has a penalty
        #Apply the most severe one (Piazza question @96)
        index_of_players_penalty = [penalty[0] for penalty in penalty_stack[concerned_team]].index(player_id)
        if RANKED_PENALTIES.index(penalty_severity) > RANKED_PENALTIES.index(penalty_stack[concerned_team][index_of_players_penalty][2]):
            if penalty_severity in ["Misconduct", "Game Misconduct"]:
                #Those penalties are more severe but the team doesn't stay shorthanded with them.
                #Since those penalties override the already announced one, we could simply delete the latter
                penalty_stack[concerned_team].pop(index_of_players_penalty)
            else:
                penalty_stack[concerned_team].pop(index_of_players_penalty)
                penalty_stack[concerned_team].append((player_id, penalty_minutes, penalty_severity, period_time))


    else: #Treat this as a penalty for a new player
        if penalty_severity in ["Misconduct", "Game Misconduct", "Penalty Shot"]:
            return penalty_stack #Only penalties of type "Minor", "Bench Minor", "Major", and "Match" can make a team
        #Short-handed. Other types of penalties exclude a particular player but allows the team to replace him
        #With someone else. Penalty shots constitute no exclusions.

        #Adding penalty to the concerned team.
        #If already 2 penalties exist, ignore the new penalty
        if len(penalty_stack[concerned_team])<2:
            penalty_stack[concerned_team].append((player_id, penalty_minutes, penalty_severity, period_time))

    old_team_on_power_play = penalty_stack["team_on_power_play"]
    #Determining who's in powerplay now
    if len(penalty_stack["home"]) > len(penalty_stack["away"]): #In this case away is on powerplay
        penalty_stack["team_on_power_play"] = "away"
    elif len(penalty_stack["home"]) < len(penalty_stack["away"]):
        penalty_stack["team_on_power_play"] = "home"
    else:
        penalty_stack["team_on_power_play"] = "none"

    #Now if the team on power play changed, we set "power_play_since" to be perod_time, else we do nothing,
    #Thus preserving the start time of the already existing power_play
    if old_team_on_power_play != penalty_stack["team_on_power_play"]:
        if penalty_stack["team_on_power_play"] == "none":
            #Makes more sense to reset "power_play_since" to zero here, although can be set
            #to anything we want.
            penalty_stack["power_play_since"] = 0
        else :
            penalty_stack["power_play_since"] =  period_time

    return penalty_stack

def penalty_stack_update_on_goal_event(penalty_stack, period_time, scoring_team, home):
    """
    Update function to be called each goal event.
    """
    #Pre-processing
    conceding_team = "away" if scoring_team==home else "home"
    scoring_team = "away" if conceding_team=="home" else "away"
    period_time = calculate_seconds(period_time)
    #If the conceding_team is short-handed, delete the minor penalty corresponding
    #to the least amount of time on the clock (Double minors with t>2 mins become minors)
    if len(penalty_stack[conceding_team]) > len(penalty_stack[scoring_team]):
        #Now create a list of minor penalties or double minors with time >2 mins
        #Here double minors with time <=2 mins have been automatically transformed to minors in previous
        #update calls.
        candidate_penalties_idxs = [i for i in range(len(penalty_stack[conceding_team])) if
                                    penalty_stack[conceding_team][i][2] in ["Minor", "Double Minor"]]
        if len(candidate_penalties_idxs) == 0:
            return penalty_stack #No Minor or Double Minor penalties to be stopped
        else:
            #Look for the penalty with the shortest time on clock (for double minor consider
            #duration = 2)
            shortest_penalty_index = candidate_penalties_idxs[0]
            shortest_penalty_time_on_clock = 2*60-\
                                             (period_time-penalty_stack[conceding_team][shortest_penalty_index][3])
            for idx in candidate_penalties_idxs:
                time_on_clock = 2*60-\
                                             (period_time-penalty_stack[conceding_team][idx][3])
                if time_on_clock<shortest_penalty_time_on_clock:
                    time_on_clock = shortest_penalty_time_on_clock
                    shortest_penalty_index = idx

            if penalty_stack[conceding_team][shortest_penalty_index][2]=="Double Minor":
                #Double Minor is replaced by a minor
                double_minor_penalty = penalty_stack[conceding_team].pop(shortest_penalty_index)
                new_minor_penalty = (double_minor_penalty[0],2,"Minor", period_time)
                penalty_stack[conceding_team].append(new_minor_penalty)
            else:
                #Just delete the minor penalty
                penalty_stack[conceding_team].pop(shortest_penalty_index)

        old_team_on_power_play = penalty_stack["team_on_power_play"]
        #Determining who's in powerplay now
        if len(penalty_stack["home"]) > len(penalty_stack["away"]): #In this case away is on powerplay
            penalty_stack["team_on_power_play"] = "away"
        elif len(penalty_stack["home"]) < len(penalty_stack["away"]):
            penalty_stack["team_on_power_play"] = "home"
        else:
            penalty_stack["team_on_power_play"] = "none"

        #Now if the team on power play changed, we set "power_play_since" to be perod_time, else we do nothing,
        #Thus preserving the start time of the already existing power_play
        if old_team_on_power_play != penalty_stack["team_on_power_play"]:
            if penalty_stack["team_on_power_play"] == "none":
                #Makes more sense to reset "power_play_since" to zero here, although can be set
                #to anything we want.
                penalty_stack["power_play_since"] = 0
            else :
                penalty_stack["power_play_since"] =  period_time




    return penalty_stack




def engineered_data_frame(data):
    """
    Takes an instance of PbPData as a parameter and returns the data it contains in pandas data frame format, including
    all the feature engineering techniques and features used in Milestone 2 Task 4.
    """
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
    Scorers = []
    Goalies = []
    Shoot_type = []
    Home = []
    Away = []
    Home_Rink = []
    #Last Event Features
    Last_Event_ID = []
    Last_Event_Type = []
    Last_Coordinate_X = []
    Last_Coordinate_Y = []
    Last_Period = []
    Last_Period_Time = []
    Last_Time = []
    #Powerplay features
    Powerplay_Since = []
    Friendly_Non_Goalies = []
    Opponent_Non_Goalies = []

    penalty_stack = reset_penalty_stack()
    for a in range(len(data.data)):
        for b in range(len(data.data[a]['data'])):
            for i in range(len(data.data[a]['data'][b]['liveData']['plays']['allPlays'])):
                if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'] == 'Period Start':
                    penalty_stack = reset_penalty_stack()
                #Make the on any event update to delete outdated penalties
                penalty_stack = penalty_stack_update_on_any_event(
                    penalty_stack,
                    data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['periodTime']
                )
                if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'] == 'Shot' or data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'] == 'Goal':
                    #Features corresponding to last event
                    Last_Event_ID.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['about']['eventIdx'])
                    Last_Event_Type.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['result']['event'])
                    Last_Coordinate_X.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['coordinates'].get('x', np.nan))
                    Last_Coordinate_Y.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['coordinates'].get('y', np.nan))
                    Last_Period.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['about']['period'])
                    Last_Period_Time.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['about']['periodTime'])
                    Last_Time.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i-1]['about']['dateTime'])
                    #Features corresponding to current event
                    Game_ID.append(data.data[a]['data'][b]['gamePk'])
                    Game_Type.append(data.data[a]['data'][b]['gameData']['game']['type'])
                    Event_ID.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['eventIdx'])
                    Event_Type.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'])
                    Home.append(data.data[a]['data'][b]['gameData']['teams']['home']['name'])
                    Away.append(data.data[a]['data'][b]['gameData']['teams']['away']['name'])
                    if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['periodType'] =='SHOOTOUT':
                        Home_Rink.append(np.nan)
                    else:
                        Home_Rink.append(data.data[a]['data'][b]['liveData']['linescore']['periods'][data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['period']-1]['home'].get('rinkSide', np.nan))

                    if 'strength' in data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result'].keys():
                        Power_Game.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['strength']['name'])
                    else:
                        Power_Game.append(np.nan)

                    if 'emptyNet' in data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result'].keys():
                        Empty_Net.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['emptyNet'])
                    else:
                        Empty_Net.append(np.nan)
                    Team_Attack.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['team']['name'])
                    Coordinate_X.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['coordinates'].get('x', np.nan))
                    Coordinate_Y.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['coordinates'].get('y', np.nan))
                    Period.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['period'])
                    Period_Time.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['periodTime'])
                    Time.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['dateTime'])
                    Shoot_type.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result'].get('secondaryType', np.nan))

                    for j in range(len(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'])):
                            if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['playerType'] == 'Shooter':
                                Shooters.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['player']['fullName'])
                            if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['playerType'] == 'Scorer':
                                Shooters.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['player']['fullName'])
                            if data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['playerType'] == 'Goalie':
                                Goalies.append(data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][j]['player']['fullName'])

                    #Add data related to penalties
                    period_time = Period_Time[-1]
                    period_time = calculate_seconds(period_time)
                    if penalty_stack["power_play_since"]== 0:
                        Powerplay_Since.append(0)
                    else:
                        Powerplay_Since.append(period_time-penalty_stack["power_play_since"])
                    team_attack_is = "home" if Team_Attack[-1]==Home[-1] else "away"
                    team_opponent_is = "home" if team_attack_is=="away" else "away"
                    Friendly_Non_Goalies.append(5-len(penalty_stack[team_attack_is]))
                    Opponent_Non_Goalies.append(5-len(penalty_stack[team_opponent_is]))
                    #Now, if the shot was actually a goal, update the penalt_stack according
                    #To the rule of deleting a minor penalty when opponent scores
                    if Event_Type[-1]=='Goal':
                        penalty_stack = penalty_stack_update_on_goal_event(
                            penalty_stack,
                            Period_Time[-1],
                            Team_Attack[-1],
                            Home[-1]
                        )
                elif data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['event'] == 'Penalty':
                    penalty_stack = penalty_stack_update_on_penalty_event(
                        penalty_stack,
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['penaltySeverity'],
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['result']['penaltyMinutes'],
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['about']['periodTime'],
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['players'][0]['player']['id'],
                        data.data[a]['data'][b]['liveData']['plays']['allPlays'][i]['team']['name'],
                        data.data[a]['data'][b]['gameData']['teams']['home']['name'])

                if len(Goalies) < len(Game_ID):
                    Goalies.append(np.nan)


    data_game = {'Game_ID': Game_ID, 'Game_Type': Game_Type, 'Event_ID': Event_ID, 'Last_Event_ID': Last_Event_ID,
                 'Home_Team': Home, 'Home_Rink': Home_Rink, 'Away_Team': Away, 'Event_Type': Event_Type,
                 'Last_Event_Type': Last_Event_Type, 'Shoot_Type': Shoot_type, 'Time': Time, 'Period': Period,
                 'Last_Period': Last_Period, 'Period_Time': Period_Time, 'Last_Period_Time': Last_Period_Time,
                 'Team_Attack': Team_Attack, 'Power_Game': Power_Game, 'Empty_Net': Empty_Net,
                 'Shooters_scorer': Shooters, 'Goalies': Goalies, 'X_Coordinate': Coordinate_X,
                 'Last_Coordinate_X': Last_Coordinate_X, 'Y_Coordinate': Coordinate_Y,
                 'Last_Coordinate_Y': Last_Coordinate_Y, 'Powerplay_Since': Powerplay_Since,
                 'Friendly_Non_Goalies': Friendly_Non_Goalies, 'Opponent_Non_Goalies': Opponent_Non_Goalies}
    df = pd.DataFrame(data_game)
    df["Powerplay_Since"] = df.Powerplay_Since.map(lambda x: f'{x//60:02d}:{x%60:02d}')

    #Adding Other features required for part 4 of milesone 2.
    # Convert Period times to number of seconds
    df['Period_Time_Seconds'] = df.Period_Time.map(calculate_seconds)
    df['Last_Period_Time_Seconds'] = df.Last_Period_Time.map(calculate_seconds)
    df['Time_Between_Events'] = df['Period_Time_Seconds'] - df['Last_Period_Time_Seconds']
    # Transform X coordinates to one side of the rink
    df['X_Transformed'] = df.apply(transform_X, axis=1)
    # Transform Last Coordinates X to one side of the rink
    df['Last_X_Transformed'] = df.apply(transform_last_X, axis=1)
    # Get the distance between all pairs of events and preceding events
    df['Distance'] = df.apply(get_distance, axis=1)
    # Creat a boolean column testing whether the last event type was a shot
    df['Rebond'] = df['Last_Event_Type'] == 'Shot'
    # Set the angles of the events
    df['Angle'] = df.apply(get_angle, axis=1)
    # Set a column for the angles of the last events that were shots
    df['Last_Angle'] = df.apply(get_last_angle, axis=1)
    # Compute the angular difference between the angle of the present event and the angle of the last events (both shots).
    df['Delta_Angle'] = df['Angle'] - df['Last_Angle']
    # Compute the speed between an event and a last event
    df['Speed'] = df['Distance'] / df['Time_Between_Events']

    return df

