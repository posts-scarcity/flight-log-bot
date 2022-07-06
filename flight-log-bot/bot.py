import tweepy
import json
import pandas as pd
from . import CONFIG

class Client(tweepy.Client):
    def __init__(self, bearer_token=None, consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, wait_on_rate_limit=False):
        super().__init__()
        self.bearer_token = bearer_token
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.wait_on_rate_limit = wait_on_rate_limit


class Listener(tweepy.StreamingClient):
    def __init__(self, bearer_token, client):
        super().__init__(bearer_token)
        self.bearer_token = bearer_token
        self.client = client
        self.ids = self.get_ids()
        rulelist = []
        for u in self.ids:
            rulelist.append(tweepy.StreamRule(f'from:{u}'))
        self.add_rules(rulelist)
        print('Rule list submitted. Rules:')
        print(self.get_rules())

    def get_ids(self):
        print('Reading CSV.')
        df = pd.read_csv(CONFIG['csv'])
        self.df = df[df.Handle.notna()].copy()
        print('Looking up IDs by username...')
        users = self.client.get_users(usernames=self.df['Handle'].tolist())
        print('Getting user account IDs from list of handles...')
        self.df['id'] = self.df.apply(lambda row: self.apply_ids(row, users), axis=1)
        print('Done. Saving IDs...')
        # need a way to preserve IDs instead of handles (handles can change, IDs do not)
        self.df.to_csv(CONFIG['working'])
        return self.df['Handle'].tolist()

    def apply_ids(self, row, users):
        for user in users:
            if (row['id'] == 0):
                if user[0].data['username'] == row['Handle']:
                    return user[0].data['id']

    def on_tweet(self, tweet):
        print(f"[tweet {tweet.created_at}] {tweet.user.name}:{tweet.text}")
        num_flights = self.df.loc[self.df['id'] == tweet.user.id, 'Total'].item()
        user_name = self.df.loc[self.df['id'] == tweet.user.id, 'Name'].item()
        print(f'URL: https://twitter.com/{tweet.user.name}/{tweet.id_str}')
        print(f"According to court releases and FOIA'd flight logs, {user_name} took {num_flights} with Jeffrey Epstein.")

    def on_exception(self, exception):
        print(f"Exception: {exception}")


def main():
    client = Client(bearer_token=CONFIG['BEARER_TOKEN'],
                    consumer_key=CONFIG['API_KEY'],
                    consumer_secret=CONFIG['API_SECRET'],
                    access_token=CONFIG['ACCESS_TOKEN'],
                    access_token_secret=CONFIG['ACCESS_SECRET'],
                    wait_on_rate_limit=True)
    listener = Listener(bearer_token=CONFIG['BEARER_TOKEN'], client=client)
    while True:
        try:
            pass
        except KeyboardInterrupt:
            print('\nEnded by user.')
            exit(0)


if __name__ == '__main__':
    main()
