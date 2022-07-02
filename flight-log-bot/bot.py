import os
from dotenv import load_dotenv, find_dotenv
import tweepy

class MyStreamListener(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        self.me = api.me()

    def on_status(self, tweet):
        print(f"{tweet.user.name}:{tweet.text}")

    def on_error(self, status):
        print("Error detected")

def setup_env():
    load_dotenv(find_dotenv())

def setup_followlist():
    return []

def get_auth_tweepy():
    auth = tweepy.OAuthHandler(os.getenv('API_KEY'),
                               os.getenv('API_SECRET'))
    auth.set_access_token(os.getenv('ACCESS_TOKEN'),
                               os.getenv('ACCESS_SECRET'))
    return tweepy.API(auth, wait_on_rate_limit=True,
                      wait_on_rate_limit_notify=True)

def start_stream(api, tweets_listener):
    return tweepy.Stream(auth=api.auth,
                         listener=tweets_listener)


def main():
    setup_env()
    api = get_auth_tweepy()
    followlist = setup_followlist()
    tweets_listener = MyStreamListener(api)
    stream = start_stream(api, tweets_listener)
    stream.filter(follow=followlist)


if __name__=='__main__':
    main()