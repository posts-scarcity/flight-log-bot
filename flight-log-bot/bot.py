from tweepy import Client, StreamingClient, StreamRule, errors
from pandas import read_csv
from numpy import isnan
from time import sleep
from datetime import datetime, timedelta
from . import CONFIG


class Client(Client):
    def __init__(self, bearer_token=None, consumer_key=None, consumer_secret=None, access_token=None, access_token_secret=None, wait_on_rate_limit=False):
        super().__init__()
        self.bearer_token = bearer_token
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.wait_on_rate_limit = wait_on_rate_limit
    
    def test_tweet(self, qt, text='Testing hello 123'):
        self.create_tweet(quote_tweet_id=qt, text=text)


class Listener(StreamingClient):
    def __init__(self, bearer_token, client, wait_on_rate_limit):
        super().__init__(bearer_token)
        self.bearer_token = bearer_token
        self.client = client
        self.ids = self.get_ids()
        self.clear_rules()
        self.setup_rules()

    def get_ids(self):
        print('Reading CSV.')
        df = read_csv(CONFIG['csv'])
        self.df = df[df.Handle.notna()].copy() # only rows with Handles will be tracked
        self.df.id = self.df.id.astype(int)
        self.df.index.name = 'Index'
        print('Checking user IDs...')
        noid = self.df['id'].isnull().copy()
        noid = self.df[noid]
        if noid.values.any():
            ids = noid['Handle'].tolist()
            print(f'Getting missing user IDs for {ids}...')
            users = self.client.get_users(usernames=ids)
            print(users)
            print('Writing found IDs to dataframe...')
            self.df['id'] = self.df.apply(lambda row: self.apply_ids(row, users), axis=1)
        print('Done. Saving dataframe...')
        # need a way to preserve IDs instead of handles (handles can change, IDs do not)
        self.df.to_csv(CONFIG['working'])
        return self.df['id'].tolist()

    def apply_ids(self, row, users):
        for user in users.data:
            if isnan(row['id']):
                if user['username'] == row['Handle']:
                    return user['id']

    def setup_rules(self):
        rulelist = []
        for u in self.ids:
            rulelist.append(StreamRule(f'from:{u}'))
        try:
            self.add_rules(rulelist)
        except errors.HTTPException as e:
            print(f'HTTPException: {e}')
            now = datetime.now()
            print(f'Waiting 15 minutes before trying again (CTRL+C to cancel).\nIt is now: {now}\n2nd try at {now+timedelta(seconds=900)}')
            sleep(900)
            self.add_rules(rulelist)
        print('Filter rule list submitted. Rules:')
        print(self.get_rules())

    def get_handle(self, id):
        user = self.client.get_user(id=id, user_fields='location')
        return user.data

    def on_tweet(self, tweet):
        user = self.get_handle(tweet.author_id)
        print(tweet.data)
        print(f"[{tweet.created_at}] {user.name} (@{user.username}): {tweet.text}")
        num_flights = self.df.loc[self.df['id'] == tweet.author_id, 'Total'].item()
        user_name = self.df.loc[self.df['id'] == tweet.author_id, 'Name'].item()
        url = f'https://twitter.com/{user.username}/status/{tweet.id}'
        s = 's' if num_flights == 1 else ''
        text = f"According to court releases and FOIA'd flight logs, {user_name} was on at least {num_flights} flight{s} with Jeffrey Epstein between 1995 and 2005."
        print(f'URL: {url}')
        print(text)
        if 'in_reply_to_user_id' in tweet.data:
            # this is the reply/thread case
            pass
        elif 'RT @' in tweet.text:
            # this is the retweet case
            pass
        else:
            if CONFIG['make_tweets']:
                self.client.self.create_tweet(quote_tweet_id=tweet.id, text=text)

    def on_exception(self, exception):
        print(f"Caught unknown exception {exception}")

    def clear_rules(self):
        rulelist = []
        rules = self.get_rules()
        if rules.data == None:
            print('No stream rules active.')
        else:
            print('Rules still exist:')
            print(rules)
            for rule in rules.data:
                rulelist.append(rule.id)
            self.delete_rules(ids=rulelist)
            rules = self.get_rules()
            print('Stream rules deleted.')


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
    try:
        listener.filter(expansions='author_id,in_reply_to_user_id',
                        tweet_fields='created_at,geo,source',
                        user_fields='id,name,username')
    except KeyboardInterrupt:
        print('\nEnded by user. Deleting filter rules...')
        listener.clear_rules()
        listener.disconnect()
        print('Exiting.')
        exit(0)


if __name__ == '__main__':
    main()
