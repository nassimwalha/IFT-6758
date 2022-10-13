from tqdm import tqdm
import requests
import os
import re


#Télécharge les données play-by-play de la LNH pour la saison régulière
def donwloadPlayByPlay_regularSeason(saison: int):
    #saison = la saison pour laquelle vous telechargez les donnees. For example 2016 means season 2016-2017

    try:
        #Get the game IDs for the regular season
        games = requests.get(f"https://statsapi.web.nhl.com/api/v1/schedule?season={saison}{saison + 1}&gameType=R").text
        gameIDs = re.findall(r'(?<="gamePk" : )[0-9]*(?=,)', games)
            
        #Donwload and sava play-by-play data
        for i in tqdm(gameIDs, desc="Downloading..."):
            data = requests.get(f"https://statsapi.web.nhl.com/api/v1/game/{i}/feed/live/")
        
            if(data.status_code == 200):
                #save data
                os.makedirs(f"../data/regular season/{saison}-{saison + 1}/", exist_ok = True)
                with open(f"../data/regular season/{saison}-{saison + 1}/{i}.txt", 'wb') as f:
                    f.write(data.content)
    
    except Exception as e:
        print(e)
        
        
#Télécharge les données play-by-play de la LNH pour les playoffs
def donwloadPlayByPlay_playoffs(saison: int):
    #saison = la saison pour laquelle vous telechargez les donnees. For example 2016 means season 2016-2017

    try:
        #Get the game IDs for the playoffs
        games = requests.get(f"https://statsapi.web.nhl.com/api/v1/schedule?season={saison}{saison + 1}&gameType=P").text
        gameIDs = re.findall(r'(?<="gamePk" : )[0-9]*(?=,)', games)
        
        #Donwload and sava play-by-play data
        for i in tqdm(gameIDs, desc="Downloading..."):
            data = requests.get(f"https://statsapi.web.nhl.com/api/v1/game/{i}/feed/live/")
        
            if(data.status_code == 200):        
                #save data
                os.makedirs(f"../data/playoffs/{saison}-{saison + 1}/", exist_ok = True)
                with open(f"../data/playoffs/{saison}-{saison + 1}/{i}.txt", 'wb') as f:
                    f.write(data.content)
    
    except Exception as e:
        print(e)   
       
              
    
if __name__ == "__main__":
    list=[2016, 2017, 2018, 2019, 2020]###############################
    
    for i in list:#####################################################
        donwloadPlayByPlay_regularSeason(i)###########################
        donwloadPlayByPlay_playoffs(i)###########################
