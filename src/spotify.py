import datetime
import requests
import webbrowser
from urllib.parse import urlencode
from src.config import client_id,client_secret, redirect_uri

import dotenv
dotenv.load_dotenv()





def get_auth():
    '''
    Calls for user login in order to get later access token
    '''

    
    mother_link = "https://accounts.spotify.com/authorize"
    query_params = urlencode({"response_type": 'code',
                                'redirect_uri': redirect_uri,
                                'show_dialog':True,
                                'scope':'user-read-playback-state user-follow-read user-follow-modify user-top-read user-modify-playback-state user-read-private playlist-modify-private playlist-modify-public',
                                "client_id": client_id})
    
    lookup_url = f"{mother_link}?{query_params}"
    r = requests.get(lookup_url)
    webbrowser.open(lookup_url, new=0)

    return client_id

    

def get_first_token(code):

    '''
    Fetches Spotify access token after code received in callback endpoint
    '''

    mother_link='https://accounts.spotify.com/api/token'
    key={'code':code,
            "grant_type": "authorization_code",
            "client_id": client_id,"client_secret": client_secret,
            'redirect_uri':redirect_uri}
    
    r = requests.post(mother_link,data=key)
    
    if r.status_code not in range(200, 299):
        raise Exception("Could not authenticate client.")
    else:
        print('Correct input code')
    
    data = r.json()
    now = datetime.datetime.now()
    access_token = data['access_token']
    expires_in = data['expires_in'] # seconds
    refresh_token=data['refresh_token']
    expires = now + datetime.timedelta(seconds=expires_in)
    access_token_expires = expires
    access_token_did_expire = expires < now

    answer = [access_token, refresh_token, access_token_expires, access_token_did_expire]

    return answer






def get_resource_header(access_token, access_token_expires , refresh_token):
    '''
    Generate header for any Spotify API request
    '''
    access_token, access_token_expires = get_access_token(access_token, access_token_expires, refresh_token)
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    return headers, access_token, access_token_expires


def get_access_token(access_token, access_token_expires, refresh_token):

    '''
    Checks if current access token is expired, and if so, gets new access token with refresh token
    '''

    now = datetime.datetime.now()
    if access_token_expires < now:
        return update_token(refresh_token)
    elif access_token == None:
        return update_token(refresh_token)
    return access_token, access_token_expires


def update_token(refresh_token):
    '''
    Gets new access token in case old access token is expired.
    Args:
        refresh_token (str): refresh token
    Return:
        access_token(str): new access token ready to use
        access_token_expires (datetime): time when new access token expires
    '''
    mother_link='https://accounts.spotify.com/api/token'
    key={"grant_type": "refresh_token",
            "client_id": client_id,"client_secret": client_secret,
            'refresh_token':refresh_token}

    r = requests.post(mother_link,data=key)  
    data = r.json()

    now = datetime.datetime.now()
    access_token = data['access_token']
    
    expires_in = data['expires_in'] # seconds
    access_token_expires = now + datetime.timedelta(seconds=expires_in)
    
    access_token_did_expire = access_token_expires < now
    return access_token, access_token_expires


################################################################################################
     
def get_my_user_info(headers):
    '''
    Retrieves from Spotify all information related to the user
    Args:
    
    Returns:
        r.json()(json file): json with all the data from Spotify 
    '''
    

    endpoint = f'https://api.spotify.com/v1/me'
    
    r = requests.get(endpoint,headers=headers)
    
    return r.json()

def get_top_50(time_range, headers, limit=50):
    
    '''
    Collects user top50 spotify songs based on a given time_range.
    Args:
        time_range(str): Either 'short_term', 'medium_term' or 'long term'
        limit(int): number of top song. By default,50. Spotify limits number to 50,
        if more than 50 is required, several requests should be perform with an offset.
        Here only 50.

    Returns:
        top_50_list(list): list of song ids
    
    '''
    
    top_50_list = []
    
    
    endpoint = f"https://api.spotify.com/v1/me/top/tracks"
    
    query_params = urlencode({"limit": limit, 'time_range': time_range})
    lookup_url = f"{endpoint}?{query_params}"
    
    r = requests.get(lookup_url,headers=headers)
    
    data = r.json()

    for pos,song in enumerate(data['items']):
        uri_id = song['id']
        

        top_50_list.append(uri_id)
        
    return top_50_list


def _get_json_song(headers, song_id, country = None):
    """
    Retrieves from Spotify information related to song
    Args:
        song_id : Spotify song id
    Returns (json): json with song information
    """
    
    endpoint = f'https://api.spotify.com/v1/tracks/{song_id}'
    

    if country is None:
        r = requests.get(endpoint, headers=headers)
    else:
        params = {'market':country}
        r = requests.get(endpoint, headers=headers, params = params)


    
    return r.json()

def create_playlist(headers, users):
    '''
    Creates playlist for a specific user
    Args:
        headers (dict) : spotify api headers
        users(list): list of user ids for party playlist. first userid is the login user.
    Returns (json): json with generated playlist

    
    '''

    user_id = users[0]

    endpoint = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    string = ' ft. '.join(users)
    headers['Content-Type'] = 'application/json'

    playlist_name = f'SpotiFeat Mix {string}'
    params = {'user_id': user_id}
    data = {'name': playlist_name, 'public': False, 'collaborative': True}

    r = requests.post(endpoint, headers = headers, json = data)


    return r.json()

def add_songs_to_playlist(playlist_id, song_id_list, headers):
    '''
    Add songs to a specific playlist
    Args:
        playlist_id (str) : specific playlist id
        song_id_list(list): list of song ids to add to playlist
    Returns (json): json with request response


    '''

    #entra lista de ids a meter de golpe

    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks' 

    
    headers['Content-Type'] = 'application/json'

    uris_list = list(map(lambda x: f'spotify:track:{x}', song_id_list))

    data = {'uris': uris_list}


    
    r = requests.post(endpoint, json = data, headers = headers)

    return r



def get_user_top_artist(headers, limit=20, time_range = 'long_term'):
    
    '''
    Fetches login user most favourite artist based on specific time range
    Args:
        time_range(str): Either 'short_term', 'medium_term' or 'long term'
        limit(int): number of top artists. By default,20.

    Returns:
        top_list(list): list of artist ids

    '''
    
    top_list = []
    
    
    endpoint = f"https://api.spotify.com/v1/me/top/artists"
    
    params = {'limit': limit, 'time_range': time_range}
    
    r = requests.get(endpoint,headers=headers, params=params)
    
    data = r.json()['items']

    for artist in data:
        artist_id = artist['id']
        

        top_list.append(artist_id)
        
    return top_list

def get_artist_related(artist_id, headers):

    '''
    Fetches from spotify api info related to artists related to a specific artist
    Args:
        artist_id(str): specific artist id

    Returns:
        Returns (json): json with request response

    '''

    endpoint = f'https://api.spotify.com/v1/artists/{artist_id}/related-artists'
    

    r = requests.get(endpoint,headers=headers)

    return r.json()


def get_artist_info(artist_id, headers):

    '''
    Fetches from spotify api info related to a specific artist
    Args:
        artist_id(str): specific artist id

    Returns:
        Returns (json): json with request response

    '''


    endpoint = f'https://api.spotify.com/v1/artists/{artist_id}'
    

    r = requests.get(endpoint,headers=headers)

    return r.json()


def get_album_info(headers, album_id):

    endpoint = f'https://api.spotify.com/v1/albums/{album_id}'

    r = requests.get(endpoint,headers=headers)

    return r.json()


def check_follow(headers, user_id):

    endpoint = f'https://api.spotify.com/v1/me/following/contains'

    params = {'type': 'user', 'ids': user_id}

    r = requests.get(endpoint,headers=headers, params = params)

    return r.json()


def follow_user(headers, user_id):

    endpoint = f'https://api.spotify.com/v1/me/following'

    params = {'type': 'user', 'ids': user_id}

    r = requests.put(endpoint,headers=headers, params = params)

    return r


def unfollow_user(headers, user_id):

    endpoint = f'https://api.spotify.com/v1/me/following'

    params = {'type': 'user', 'ids': user_id}

    r = requests.delete(endpoint,headers=headers, params = params)

    return r





class SpotifyAdmin():

    

    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    first_token=None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redirect_uri='https://www.google.com/'
        self.code=None
        self.client_id=client_id
        self.client_secret=client_secret
        self.check_auth()
        
        
        '''self.avail_countries=['DZ','EG','MA','ZA','TN','BH','HK','IN','RI','IL','JP','JO','KW','LB','MY','OM','PS',
        'PI','QA','SA','SG','TW','TH','AE','VN','AD','AT','BE','BG','CY','CZ','DK','EE','FI','FR','DE','GR','HU',
        'IS','IE','IT','LV','LI','LT','LU','MT','MC','NL','NO','PL','PT','RO','SK','ES','SE','CH','TR','UK','RU',
        'BY','KZ','MD','UA','AL','BA','HR','ME','MK','RS','SI','XK','CA','CR','DO','SV','GT','HN','MX','NI','PA',
        'US','AR','BO','BR','CL','CO','EC','PY','PE','UY','AU','NZ']'''
        
        self.avail_countries=['US']
    
    
    
        self.spotify_genres=["acoustic","afrobeat","alt-rock","alternative","ambient","anime","black-metal",
        "bluegrass","blues","bossanova","brazil","breakbeat","british","cantopop","chicago-house","children",
        "chill","classical","club","comedy","country","dance","dancehall","death-metal","deep-house","detroit-techno",
        "disco","disney","drum-and-bass","dub","dubstep","edm","electro","electronic","emo","folk","forro","french",
        "funk","garage","german","gospel","goth","grindcore","groove","grunge","guitar","happy","hard-rock","hardcore",
        "hardstyle","heavy-metal","hip-hop","holidays","honky-tonk","house","idm","indian","indie","indie-pop","industrial",
        "iranian","j-dance","j-idol","j-pop","j-rock","jazz","k-pop","kids","latin","latino","malay","mandopop","metal",
        "metal-misc","metalcore","minimal-techno","movies","mpb","new-age","new-release","opera","pagode","party","philippines-opm",
        "piano","pop","pop-film","post-dubstep","power-pop","progressive-house","psych-rock","punk","punk-rock","r-n-b",
        "rainy-day","reggae","reggaeton","road-trip","rock","rock-n-roll","rockabilly","romance","sad","salsa","samba",
        "sertanejo","show-tunes","singer-songwriter","ska","sleep","songwriter","soul","soundtracks","spanish","study",
        "summer","swedish","synth-pop","tango","techno","trance","trip-hop","turkish","work-out","world-music"]
              
    
    def get_auth(self):
        mother_link = "https://accounts.spotify.com/authorize"
        query_params = urlencode({"client_id": self.client_id,
                                  "response_type": 'code',
                                  'redirect_uri':self.redirect_uri,
                                  'show_dialog':True,
                                 'scope':'user-read-playback-state user-top-read user-modify-playback-state user-read-private playlist-modify-private playlist-modify-public'})
        
        lookup_url = f"{mother_link}?{query_params}"
        r = requests.get(lookup_url)
        webbrowser.open(lookup_url, new=1)
      

        
    
    def input_code(self):
        return input('Please enter code from redirected url')
    
    def get_first_token(self):
        mother_link='https://accounts.spotify.com/api/token'
        key={'code':self.code,
             "grant_type": "authorization_code",
             "client_id": self.client_id,"client_secret": self.client_secret,
             'redirect_uri':self.redirect_uri}
        r = requests.post(mother_link,data=key)
        
        if r.status_code not in range(200, 299):
            raise Exception("Could not authenticate client.")
        else:
            print('Correct input code')
        
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in'] # seconds
        refresh_token=data['refresh_token']
        self.refresh_token=refresh_token
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return access_token    
    
    def update_token(self):
        mother_link='https://accounts.spotify.com/api/token'
        key={"grant_type": "refresh_token",
             "client_id": self.client_id,"client_secret": self.client_secret,
             'refresh_token':self.refresh_token}
        r = requests.post(mother_link,data=key)  
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in'] # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return access_token
        

    def check_auth(self):
        while self.code==None:
            print('Identification is required. Please click on link below.')
            self.get_auth()
            self.code=self.input_code()
            self.first_token=self.get_first_token()
            
  
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            return self.update_token()
        elif token == None:
            return self.update_token()
        return token
        
    
    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers            
        

    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')
    
    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')
    
    def base_search(self, query_params): # type
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):  
            return {}
        return r.json()
    
    def search(self, query=None, operator=None, operator_query=None, limit_type=7,market_type='from_token',search_type='track' ):
        if query == None:
            raise Exception("A query is required")
        if isinstance(query, dict):
            query = " ".join([f"{k}:{v}" for k,v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator_query, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query,'limit':limit_type, 'market':market_type,"type": search_type.lower()})
        return self.base_search(query_params)
    
    def get_song(self, _id):
        return self.get_resource(_id, resource_type='tracks')
        
    def play_song(self,song_id,offset=0,position_ms=0):
        #pending to activate one device in case none
        key={"uris": [f'spotify:track:{song_id}'],'position_ms':position_ms,'offset':{"position":offset}}
        endpoint = f"https://api.spotify.com/v1/me/player/play"
        headers = self.get_resource_header()
        r = requests.put(endpoint, json=key,headers=headers)
        
        
    def get_device_ids(self):
        endpoint = f"https://api.spotify.com/v1/me/player/devices"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        return r.json()

    def random_position_song(self,length):
        return random.randint(0, length)
        

    def get_rand_song(self):
        try:
            query='year:'+str(self.random_year())+' genre:'+self.random_genre()
            json=self.search(query,limit_type=50,market_type=self.random_country())
            songs=json['tracks']['items']

            if len(songs)==0:
                print('Not matched results, trying a new random query')
                return self.get_rand_song()

            else:
                song=songs[self.random_position_song(len(songs))]
                return song
        except (IndexError,KeyError) as err:
            return self.get_rand_song()
        
    def get_rand_song_fix_genre(self,genre='rock'):
        try:
            query='year:'+str(self.random_year())+' genre:'+genre
            json=self.search(query,limit_type=50,market_type=self.random_country())
            songs=json['tracks']['items']

            if len(songs)==0:
                print('Not matched results, trying a new random query')
                return self.get_rand_song()

            else:
                song=songs[self.random_position_song(10)]
                return song
        except (IndexError,KeyError) as err:
            return self.get_rand_song()

    def add_song_to_playlist_fix_genre(self,playlist_id,genre='rock'):
        
        endpoint=f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks' 
        headers = self.get_resource_header()
        song_uri=self.get_rand_song_fix_genre(genre=genre)['uri']
        key={'uris':[song_uri]}
        
        r = requests.post(endpoint, json=key,headers=headers)
    
    
    
    


    def random_country(self):
        return choice(self.avail_countries)
        
    def random_year(self,start=1970,stop=2020):
        return random.randint(start, stop)
    
    def random_genre(self):
        return choice(self.spotify_genres)
    

    
    def get_playlist_info(self,playlist_id):
        info_playlist={}
        offset=0
        j=0
        while len(self.get_playlist_items(playlist_id,offset)['items'])>0:
            print(f'Getting batch {j}')
            data_list=self.get_playlist_items(playlist_id,offset)['items']
            i=0
          
            for song in data_list:
                
                data=song['track']
                artists=data['artists']
                album=data['album']
                song_dict={}
                song_dict['name']=data['name']
                song_dict['artists_name']=artists[0]['name']
                song_dict['artists_id']=artists[0]['id']
                song_dict['album_name']=album['name']
                song_dict['album_id']=album['id']
                song_dict['track_length']=data['duration_ms']
                song_dict['popularity']=data['popularity']
                song_dict['release_date']=data['album']['release_date']

                info_playlist[data['id']]=song_dict
                
                i+=1
            offset+=i
            j+=1
        return info_playlist
    
    def playlist_pause(self):
        headers = self.get_resource_header()
        endpoint = f"https://api.spotify.com/v1/me/player/pause"
        
        r = requests.put(endpoint,headers=headers) 
        
        
    def check_status_playback(self):
        headers = self.get_resource_header()
        endpoint = f"https://api.spotify.com/v1/me/player"
        
        
        r = requests.get(endpoint,headers=headers) 
        return r.json()
    
    def get_top_50(self, time_range, limit=50):
        
        '''
        Collects user top50 spotify songs based on a given time_range.
        Args:
            time_range(str): Either 'short_term', 'medium_term' or 'long term'
            limit(int): number of top song. By default,50. Spotify limits number to 50,
            if more than 50 is required, several requests should be perform with an offset.
            Here only 50.
        
        '''
        
        top_50_list = []
        
        headers = self.get_resource_header()
        endpoint = f"https://api.spotify.com/v1/me/top/tracks"
        
        query_params = urlencode({"limit": limit, 'time_range': time_range})
        lookup_url = f"{endpoint}?{query_params}"
        
        r = requests.get(lookup_url,headers=headers)
        
        data = r.json()

        for pos,song in enumerate(data['items']):
            uri_id = song['id']
            

            top_50_list.append(uri_id)
            
        return top_50_list
    
    
    def get_my_full_top_50(self):
        
        '''
        Creates a dictionary with the scores of all songs in the top_50 lists of a user for short, mid and long term.
        Args:
        
        Returns:
            top_songs_dict(dict): key are songs ids. Values are the score based on its appearance in those lists

        
        '''
        
        short_term_50 = self.get_top_50('short_term')
        medium_term_50 = self.get_top_50('medium_term')
        long_term_50 = self.get_top_50('long_term')
        
        top_songs_dict = {}
        
        
        
        sum_list = short_term_50 + medium_term_50 + long_term_50
        
        sum_list = set(sum_list)
        
        for song in sum_list:
            
            score = 0
            factor_long = 1
            factor_medium = 1
            factor_short = 1
            
            if song in long_term_50:
                pos=long_term_50.index(song)
                score += (100 - pos) * factor_long
            
            if song in medium_term_50:
                pos = medium_term_50.index(song)
                score += (100 - pos) * factor_medium
                
            if song in short_term_50:
                pos = short_term_50.index(song)
                score += (100 - pos) * factor_short
                
            top_songs_dict[song] = score
            
        top_songs_dict = {key:value for key,value in sorted(top_songs_dict.items(), key = lambda x:x[1], reverse = True)}
            
        return top_songs_dict
    
    
    def get_playlist_items_json(self,playlist_id,offset=0):
        endpoint=f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        params = {"offset": offset}
        
        
        headers = self.get_resource_header()

        r = requests.get(endpoint, headers = headers, params = params)
        
     
        return r.json()
        

    
    
    
    #yes
    def _get_json_song(self, song_id, country = None):
        """
        Retrieves from Spotify information related to song
        Args:
            song_id : Spotify song id
        Returns (json): json with song information
        """
        
        endpoint = f'https://api.spotify.com/v1/tracks/{song_id}'
        headers = self.get_resource_header()

        if country is None:
            r = requests.get(endpoint, headers=headers)
        else:
            params = {'market':country}
            r = requests.get(endpoint, headers=headers, params = params)


        
        
        return r.json()
    
    
    
    def get_artist_top_tracks_json(self, artist_id):
        

        endpoint = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks'
        
        headers = self.get_resource_header()

        params = {'country': 'ES'}
        
        r = requests.get(endpoint, headers = headers, params = params)

    
        
        return r.json()
    
    #for albums database
    def get_artist_albums_json(self, artist_id):
        
        endpoint = f'https://api.spotify.com/v1/artists/{artist_id}/albums'
        headers = self.get_resource_header()
        params = {'limit': 50}
        
        
        r = requests.get(endpoint, headers = headers, params = params)
        
        return r.json()

    def create_playlist(self, user_id, name1, name2):

        endpoint = f'https://api.spotify.com/v1/users/{user_id}/playlists'
        headers = self.get_resource_header()
        headers['Content-Type'] = 'application/json'

        playlist_name = f'Awesome Mix {name1} ft. {name2}'
        params = {'user_id': user_id}
        data = {'name': playlist_name, 'collaborative': False}

        r = requests.post(endpoint, headers = headers, json = data,)

        return r.json()

 
    
    
    def get_my_user_info(self):
        '''
        Retrieves from Spotify all information related to the user
        Args:
        
        Returns:
            r.json()(json file): json with all the data from Spotify 
        '''
        

        endpoint = f'https://api.spotify.com/v1/me'
        headers = self.get_resource_header()
        r = requests.get(endpoint,headers=headers)
        
        return r.json()


    def add_song_to_playlist(self,playlist_id, song_id_list):

        #entra lista de ids a meter de golpe

        endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks' 

        headers = self.get_resource_header()
        headers['Content-Type'] = 'application/json'

        uris_list = list(map(lambda x: f'spotify:track:{x}', song_id_list))

        data = {'uris': uris_list}


        
        r = requests.post(endpoint, json = data, headers = headers)

        return r

    def get_artist_related(self, artist_id):

        endpoint = f'https://api.spotify.com/v1/artists/{artist_id}/related-artists'
        headers = self.get_resource_header()

        r = requests.get(endpoint,headers=headers)

        return r.json()

    def get_artist_info(self, artist_id):

        endpoint = f'https://api.spotify.com/v1/artists/{artist_id}'
        headers = self.get_resource_header()

        r = requests.get(endpoint,headers=headers)

        return r.json()

    def get_album_info(self, album_id):

        endpoint = f'https://api.spotify.com/v1/albums/{album_id}'
        headers = self.get_resource_header()

        r = requests.get(endpoint,headers=headers)

        return r.json()




    




    
