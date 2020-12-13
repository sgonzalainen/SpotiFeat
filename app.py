from flask import Flask, request, render_template, session, redirect, jsonify
from src.spotifyAPI import SpotifyAPI
import time
#from flask_session import Session
import datetime
import src.spotify1 as spot
import src.dataset_functions as dataset
import base64
from io import BytesIO



app =Flask(__name__)


#sess = Session()
#sess.init_app(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'



@app.route('/')
def index():

    session['access_token'] = None
    session['access_token_expires'] = datetime.datetime.now()
    session['refresh_token'] = None
    session['access_token_did_expire'] = True

    return render_template('index.html')

@app.route('/start')
def start():
    r = spot.get_auth()

    return f""

@app.route('/callback')
def callback():

    code = request.args.get('code', -1) #this is optional

    print(code)


    answer = spot.get_first_token(code)

    print(answer)

    session['access_token'] = answer[0]
    session['access_token_expires'] = answer[2]
    session['refresh_token'] = answer[1]
    session['access_token_did_expire'] = answer[3]

    return render_template('loading.html')



    


@app.route('/intro')
def intro():

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])
    

    session['access_token'] = access_token
    session['access_token_expires'] = access_token_expires

    user_profile, user_top_songs = dataset.update_user_profile_data(headers)

    user_name = user_profile.get('name')
    user_id = user_profile.get('user_id')
    user_img = user_profile.get('img_url')


    ###this mostt likelty to be removedddd #####
    if user_img == '':
        user_img = 'https://pbs.twimg.com/media/EFIv5HzUcAAdjhl?format=png&name=360x360'



    other_users = dataset.get_all_users(user_id)
    session['other_user'] = {'list_others': other_users}


    ######## Camela distance  #######

    avg_distance, min_distance, path_distance, ref_artist = dataset.get_info_distances_artist_ref(user_id)
    ##### Popularity ########################

    avg_popularity = dataset.get_rating_popu_user(user_id)

    #### Musical Age ############################
    avg_age = dataset.get_years_user(user_id)

    
    session['ref_artist'] = ref_artist


    genre_list, values_list = dataset.genre_profile_api(user_id)

    

    session['main_user'] = {'id': user_id, 'name': user_name, 'img_url': user_img, 'avg_dis': avg_distance, 'min_dis': min_distance, 'path_dis': path_distance, 'avg_popu': avg_popularity, 'avg_age': avg_age, 'values_chart': values_list }
    
    session['chart_labels'] = genre_list


    session['matches_info'] = dataset.get_my_matches(session['main_user'].get('id'))

    
  




    
    return render_template('intro.html')




@app.route('/stats')
def stats():



    user_id = session['main_user'].get('id')

    genre_list, values_list = dataset.genre_profile_api(user_id)




    return render_template('stats.html', user_profile = session['main_user'],ref_artist = session['ref_artist'] ,chart_labels = genre_list, chart_values= values_list)

@app.route('/users/<user_id>')
def user_stats(user_id):

    main_user = session['main_user'].get('id')

    user_profile = dataset.get_full_info_user(user_id)

    avg_popularity = dataset.get_rating_popu_user(user_id)

    avg_distance, min_distance, path_distance = dataset.get_info_distances_between_users(main_user, user_id)

    path_distance = list(map(dataset.extract_url_img_by_artist_name, path_distance))

    #avg_distance, min_distance, path_distance, ref_artist = dataset.get_info_distances_artist_ref(user_id)
    avg_age = dataset.get_years_user(user_id)


    genre_list, values_list = dataset.genre_profile_api(user_id)


    user_profile['avg_dis']= avg_distance
    user_profile['min_dis']= min_distance
    user_profile['path_dis']= path_distance
    user_profile['avg_popu']= avg_popularity
    user_profile['avg_age']= avg_age
    user_profile['values_chart']= values_list

    other_users_info = session['matches_info']

    match_score = dataset.fecth_match_score(user_id, other_users_info)


    user_profile['score']= match_score






    return render_template('other_stats.html', main_user_profile = session['main_user'], user_profile = user_profile, chart_labels = genre_list, chart_values= values_list)


@app.route('/select_members')
def select_members():

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])

    main_user_id = session.get('main_user').get('id')

    other_users_info = enumerate(dataset.get_other_users_info(main_user_id))


    return render_template('select_members.html', other_users_info = other_users_info)


@app.route('/party', methods = ['POST'])
def party():

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])

    main_user_id = session.get('main_user').get('id')

    members = request.form.getlist('member')

    members.insert(0, main_user_id)

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])
    num_songs = 50 # to be changeedeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee

    song_id_list, url_playlist, stats_playlist = dataset.create_mix_playlist(headers, num_songs, members)

    info_playlist = dataset.collect_info_new_playlist(headers, song_id_list)



    return render_template('party.html', url_playlist = url_playlist, info_playlist = info_playlist, stats_playlist= stats_playlist)

@app.route('/matches')
def show_matches():


    other_users_info = session['matches_info']
    

    return render_template('matches.html', other_users_info = enumerate(other_users_info))


@app.route('/trending')
def trending_songs():

    headers, access_token, access_token_expires = spot.get_resource_header(session['access_token'], session['access_token_expires'], session['refresh_token'])
    
    info_trending = dataset.get_my_trending(headers)

    return render_template('trending.html', info_trending = enumerate(info_trending))



    



@app.route('/get_genre_profile/<user_id>')
def get_profile_api(user_id):

    

    return jsonify(dataset.genre_profile_api(user_id))









    



































app.run(debug=True)