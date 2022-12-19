import numbers

from ift6758.ift6758.client.serving_client import ServingClient
from ift6758.ift6758.client.game_client import GameClient
import streamlit as st
import pandas as pd
import numpy as np

servingClient = ServingClient()
gameClient = GameClient("0000000000")

# Remove default hamburger menu
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.title("Hockey Visualization App")

with st.sidebar:
    workspace = st.selectbox('Workspace', ('', 'nassim-walha'))
    model = st.selectbox('Model', ('', 'xgb-all', 'xgb-tuned-all'))
    version = st.selectbox('Version', ('', '1.0.0'))

    if st.button('Get model'):
        form_validation = st.caption('')
        if workspace == "":
            form_validation.caption('<p style="color:red;">Select workspace<p/>', unsafe_allow_html=True)
        elif model == "":
            form_validation.caption('<p style="color:red;">Select model<p/>', unsafe_allow_html=True)
        elif version == "":
            form_validation.caption('<p style="color:red;">Select version<p/>', unsafe_allow_html=True)
        else:
            try:
                form_validation.caption(
                    f"<p style='color:red;'>{servingClient.download_registry_model(workspace, model, version)}</p>",
                    unsafe_allow_html=True)
            except Exception as e:
                form_validation.caption(f"<p style='color:red;'>Error:{e}<p/>", unsafe_allow_html=True)

with st.container():
    current_game_id = ""
    # gameId = st.selectbox('Game ID', ('', '2021020329', '2021020328', '2021020327'))
    gameId = st.text_input('Game ID', '2021020329')
    if st.button('Ping game'):
        form_valid = st.caption('')
        if gameId != current_game_id:
            try:
                gameClient = GameClient(gameId)
                current_game_id = gameId
                gameClient.ping_game()
            except Exception as e:
                form_valid.caption(f'<p style="color:red;">{e}<p/>', unsafe_allow_html=True)

with st.container():
    period = ""
    if gameClient.period is not None:
        period = gameClient.period

    timeLeft = ""
    if gameClient.time_left_in_period is not None:
        timeLeft = gameClient.time_left_in_period

    homeTeam = ""
    if gameClient.home is not None:
        homeTeam = gameClient.home

    awayTeam = ""
    if gameClient.away is not None:
        awayTeam = gameClient.away

    st.subheader(f'Game {gameId}: {homeTeam} vs {awayTeam}')
    st.markdown(f"Period **{period}** - **{timeLeft}** left")

    col1, col2 = st.columns(2)
    st.markdown("""
        <style>
        [data-testid=column]:nth-of-type(1) [data-testid=stVerticalBlock]{
            gap: 0rem;
        },
        </style>
        """, unsafe_allow_html=True)

    with col1:
        st.markdown(f"**{homeTeam}** xG(actual)")
        if gameClient.home_sum_of_expected_goals != 0 and gameClient.home_goals is not None:
            st.markdown(
                f'<p style="font-weight:bold;font-size:30px">{gameClient.home_sum_of_expected_goals}({gameClient.home_goals})</p>',
                unsafe_allow_html=True)

        goal_diff = ""
        arrow = ""
        if gameClient.home_goals is not None:
            goal_diff = abs(gameClient.home_sum_of_expected_goals - gameClient.home_goals)
            if gameClient.home_sum_of_expected_goals < gameClient.home_goals:
                arrow = "↑"
            if gameClient.home_sum_of_expected_goals > gameClient.home_goals:
                arrow = "↓"

        st.caption(f"{arrow}{goal_diff}")

    st.markdown("""
            <style>
            [data-testid=column]:nth-of-type(2) [data-testid=stVerticalBlock]{
                gap: 0rem;
            },
            </style>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"**{awayTeam}** xG(actual)")

        if gameClient.away_sum_of_expected_goals != 0 and gameClient.away_goals is not None:
            st.markdown(
                f'<p style="font-weight:bold;font-size:30px">{gameClient.away_sum_of_expected_goals}({gameClient.away_goals})</p>',
                unsafe_allow_html=True)

        goal_diff = ""
        arrow = ""
        if gameClient.away_goals is not None:
            goal_diff = abs(gameClient.away_sum_of_expected_goals - gameClient.away_goals)
            if gameClient.away_sum_of_expected_goals < gameClient.away_goals:
                arrow = "↑"
            if gameClient.away_sum_of_expected_goals > gameClient.away_goals:
                arrow = "↓"

        st.caption(f"{arrow}{goal_diff}")

with st.container():
    st.subheader('Data used for predictions (and predictions)')
    st.write(gameClient.df)

    # DATE_COLUMN = 'date/time'  ###############################################################################
    # DATA_URL = ('https://s3-us-west-2.amazonaws.com/'  #########################################################
    #            'streamlit-demo-data/uber-raw-data-sep14.csv.gz')  #################################################

    ####################################################################################################################
    # @st.cache
    # def load_data(nrows):
    #    data = pd.read_csv(DATA_URL, nrows=nrows)
    #    lowercase = lambda x: str(x).lower()
    #    data.rename(lowercase, axis='columns', inplace=True)
    #    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
    #    return data

    # Create a text element and let the reader know the data is loading.
    # data_load_state = st.caption('Loading data...')
    # Load 10,000 rows of data into the dataframe.
    # data = load_data(10000)
    # Notify the reader that the data was successfully loaded.
    # st.write(data)
    # data_load_state.caption('')
#################################################################################################################
############################################## TEST ############################################################
# option = st.selectbox(
#    'How would you like to be contacted?',
#    ('Email', 'Home phone', 'Mobile phone'))

# st.write('You selected:', option)

# if st.button('Say hello'):
#    st.write('Why hello there')
# else:
#    st.write('Goodbye')

# title = st.text_input('Movie title', 'Life of Brian')
# st.write('The current movie title is', title)

# DATE_COLUMN = 'date/time'
# DATA_URL = ('https://s3-us-west-2.amazonaws.com/'
#            'streamlit-demo-data/uber-raw-data-sep14.csv.gz')


# @st.cache
# def load_data(nrows):
#    data = pd.read_csv(DATA_URL, nrows=nrows)
#    lowercase = lambda x: str(x).lower()
#    data.rename(lowercase, axis='columns', inplace=True)
#    data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN])
#    return data


# Create a text element and let the reader know the data is loading.
# data_load_state = st.text('Loading data...')
# Load 10,000 rows of data into the dataframe.
# data = load_data(10000)
# Notify the reader that the data was successfully loaded.
# data_load_state.text('Loading data...done!')
# data_load_state.text("Done! (using st.cache)")

# if st.checkbox('Show raw data'):
#    st.subheader('Raw data')
#    st.write(data)
# st.subheader('Number of pickups by hour')
# hist_values = np.histogram(data[DATE_COLUMN].dt.hour, bins=24, range=(0, 24))[0]
# st.bar_chart(hist_values)
# st.subheader('Map of all pickups')
# st.map(data)
# hour_to_filter = st.slider('hour', 0, 23, 17)  # min: 0h, max: 23h, default: 17h
# filtered_data = data[data[DATE_COLUMN].dt.hour == hour_to_filter]
# st.subheader(f'Map of all pickups at {hour_to_filter}:00')
# st.map(filtered_data)
#################################################################################################################
