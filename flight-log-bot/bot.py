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
        self.filter(expansions='author_id,in_reply_to_user_id',
                    tweet_fields='created_at,geo,source',
                    user_fields='id,name,username')
        print('Listening...')

    def get_ids(self):
        print('Reading CSV.')
        df = pd.read_csv(CONFIG['csv'])
        self.df = df[df.Handle.notna()].copy() # only rows with Handles will be tracked
        self.df.index.name = 'Index'
        print('Checking user IDs...')
        if self.df['id'].isnull().values.any():
            print('Getting missing user IDs...')
            users = self.client.get_users(usernames=self.df[df.id.isna()]['Handle'].tolist())
            print('Writing found IDs to dataframe...')
            self.df['id'] = self.df.apply(lambda row: self.apply_ids(row, users), axis=1)
        print('Done. Saving dataframe...')
        # need a way to preserve IDs instead of handles (handles can change, IDs do not)
        self.df.to_csv(CONFIG['working'])
        return self.df['id'].tolist()

    def apply_ids(self, row, users):
        for user in users:
            if (row['id'] == 0):
                if user[0].data['username'] == row['Handle']:
                    return user[0].data['id']

    def get_handle(self, id):
        user = self.client.get_user(id=id,
                                    user_fields='location')
        return user.data

    def on_tweet(self, tweet):
        user = self.get_handle(tweet.author_id)
        print(tweet.data)
        print(f"[{tweet.created_at}] {user.name} (@{user.username}): {tweet.text}")
        num_flights = self.df.loc[self.df['id'] == tweet.author_id, 'Total'].item()
        user_name = self.df.loc[self.df['id'] == tweet.author_id, 'Name'].item()
        url = f'https://twitter.com/{user.username}/status/{tweet.id}'
        print(f'URL: {url}')
        print(f"According to court releases and FOIA'd flight logs, {user_name} was on {num_flights} flights with Jeffrey Epstein.")
        if ('in_reply_to_user_id' in tweet.data):
            # this is the organic case
            pass
        else:
            # this is the reply/thread case
            pass

    # def on_response(self, response):
    #     print(f'Response: {response}')

    # def on_exception(self, exception):
    #     print("Exception:")
    #     print(exception)


def main():
    client = Client(bearer_token=CONFIG['BEARER_TOKEN'],
                    consumer_key=CONFIG['API_KEY'],
                    consumer_secret=CONFIG['API_SECRET'],
                    access_token=CONFIG['ACCESS_TOKEN'],
                    access_token_secret=CONFIG['ACCESS_SECRET'],
                    wait_on_rate_limit=True)
    listener = Listener(bearer_token=CONFIG['BEARER_TOKEN'],
                        client=client,
                        wait_on_rate_limit=True)
    print('Listening...')
    while True:
        try:
            pass
        except KeyboardInterrupt:
            print('\nEnded by user. Deleting rules...')
            rulelist = []
            rules = listener.get_rules()
            print(rules)
            for rule in rules.data:
                rulelist.append(rule.id)
            listener.delete_rules(ids=rulelist)
            rules = listener.get_rules()
            if rules.result_count == 0:
                print('All rules deleted. Exiting.')
            else:
                print('Rules still exist:')
                print(rules)
                print('Exiting.')
                listener.disconnect()
            exit(0)


if __name__ == '__main__':
    main()
