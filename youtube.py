import argparse
import os.path
import time
from ConfigParser import SafeConfigParser
from datetime import datetime

import httplib2

# Google Data API
from googleapiclient.discovery import build
import oauth2client
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow

def create_youtube_service(config):
    youtube_read_write_scope = "https://www.googleapis.com/auth/youtube"
    youtube_api_service_name = "youtube"
    youtube_api_version = "v3"
    client_secrets_file = get_script_dir() + "client_secrets.json"
    missing_secrets_message = "Error: {0} is missing".format(
        client_secrets_file
    )
    redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    # Do OAuth2 authentication
    flow = flow_from_clientsecrets(
        client_secrets_file,
        message=missing_secrets_message,
        scope=youtube_read_write_scope,
        redirect_uri=redirect_uri
    )

    storage = Storage(get_script_dir() + "oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[oauth2client.tools.argparser],
        )
        flags = parser.parse_args()

        credentials = run_flow(flow, storage, flags)

    return build(
        youtube_api_service_name,
        youtube_api_version,
        developerKey=config['api_key'],
        http=credentials.authorize(httplib2.Http())
    )


def create_youtube_playlist(youtube, title, description):
    playlist_creating_response = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title=title,
                description=description
            ),
            status=dict(
                privacyStatus="public"
            )
        ),
        fields="id"
    ).execute()

    playlist_id = playlist_creating_response['id']
    playlist_url = get_playlist_url(playlist_id)

    print("New playlist added: {0}".format(title))
    print("\tID: {0}".format(playlist_id))
    print("\tURL: {0}".format(playlist_url))

    return playlist_id

def get_playlist_url(playlist_id):
    return "https://www.youtube.com/playlist?list={0}".format(playlist_id)


def add_video_to_playlist(youtube, playlist_id, video_id):

    print("\tAdding video playlist_id: " + playlist_id + " video_id: " + video_id)

    video_inserting_response = youtube.playlistItems().insert(
        part="snippet",
        body=dict(
            snippet=dict(
                playlistId=playlist_id,
                resourceId=dict(
                    kind="youtube#video",
                    videoId=video_id
                )
            )
        ),
        fields="snippet"
    ).execute()

    title = video_inserting_response['snippet']['title']

    print('\tVideo added: {0}'.format(title.encode('utf-8')))


def load_config_values():
    config_path = get_script_dir() + 'settings.cfg'
    section_account_name = 'accounts'
    section_playlist_name = 'playlist'

    if not os.path.exists(config_path):
        print ("Error: No config file found.")
        exit()

    config = SafeConfigParser()
    config.read(config_path)

    config_values = {
        'api_key': config.get(section_account_name, 'api_key'),
        'title' config.get(section_playlist_name, 'title'),
        'description' config.get(section_playlist_name, 'description'),
    }

    return config_values

def get_script_dir():
    return os.path.dirname(os.path.realpath(__file__)) + '/'

def read_songs_from_txt_file(file_name):
    lineList = [line.rstrip('\n') for line in open(file_name)]
    urls = []
    for line in lineList:
        if line.startswith('Url:'):
            parts = line.split('?')
            urls.append(parts[1])
    return urls            


def create_playlist_from_txt(youtube, title, description):
    songs = read_songs_from_txt_file('results.txt')

    playlist_id = create_youtube_playlist(youtube,title,description)

    for song in songs:
        add_video_to_playlist(youtube,playlist_id,song)

def main():
    print("### Script started at " + time.strftime("%c") + " ###\n")

    config = load_config_values()
    youtube = create_youtube_service(config)
    create_playlist_from_txt(youtube, config['title'], config['description'])

    print("### Script finished at " + time.strftime("%c") + " ###\n")


if __name__ == '__main__':
    main()