from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__version__ = '1.0.0'
__author__ = 'Robert Navas, Flomer Aduna, Charlie Bautista'

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import twitter_credentials
import pymongo
from textblob import TextBlob

import re
import tweepy

DB_HOST = 'ds259347.mlab.com'
DB_PORT = 59347
DB_USER = 'admin'
DB_PASS = 'admin123'
DB_NAME = 'heroku_d78xw6lj'

myclient = pymongo.MongoClient(DB_HOST, DB_PORT, retryWrites= False)
mydb = myclient[DB_NAME]
mydb.authenticate(DB_USER, DB_PASS)

products = mydb['products']
count = mydb['count']

class TwitterStreamer():

    def __init__(self):
        self.pos = 0
        self.neu = 0
        self.neg = 0
        self.user = ''
        self.geo_data = ''
        self.text = ''
        self.sentiment = ''
        self.flag = 0
        self.status = False
        self.click = 0
        self.twitter_link = ''
        self.keywords= {"gusto", "apply", "inquire", "need", "want", "insurance"}

    def auth_tweet_streamer(self, keywords):

        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        stream = Stream(auth, StdOutListener('data.txt'))

        stream.filter(track=keywords)

    def set_data(self, json_data):

        self.user = json_data['user']['screen_name']
        self.geo_data = json_data['user']['location']
        self.text = json_data['text']
        self.twitter_link = 'https://twitter.com/{}'.format(self.user)

        self.text = re.sub('(http\S+|@\S+|#\S+|[^\x00-\x7F ]+|[^a-zA-Z.\d\s])', '' , self.text)
        sentiment_score = TextBlob(self.text).sentiment.polarity

        if sentiment_score > 0:
            self.sentiment = 'positive'
            self.pos = count.find_one({'pos': {'$exists' : True}})
            pos_count = self.pos['pos']
            pos_count += 1
            pos_id = self.pos['_id']
            
            count.update_one({'_id': pos_id}, {'$set': {'pos': pos_count}})

        elif sentiment_score == 0:
            self.sentiment = 'neutral'
            self.neu = count.find_one({'neu': {'$exists' : True}})
            neu_count = self.neu['neu']
            neu_count += 1
            neu_id = self.neu['_id']
            
            count.update_one({'_id': neu_id}, {'$set': {'pos': neu_count}})

        else:
            self.sentiment ='negative'
            self.neg = count.find_one({'neg': {'$exists' : True}})
            neg_count = self.neg['neg']
            neg_count += 1
            neg_id = self.neg['_id']
            
            count.update_one({'_id': neg_id}, {'$set': {'pos': neg_count}})

        print('New Regex: {}'.format(self.text))

        self.flag = len(self.keywords.intersection(self.text.split()))

        print('New Length:{}'.format(self.flag))

        if TextBlob(self.text).detect_language() == 'en' or TextBlob(self.text).detect_language() == 'tl' or self.flag > 0 and len(TextBlob(self.text)) > 0:

            print(self.user)
            print(self.geo_data)
            print(self.text)
            print(self.sentiment)
            print(sentiment_score)
            print(self.status)

            user_information = {
                    'screen_name': self.user,
                    'location': self.geo_data,
                    'text': self.text,
                    'sentiment': self.sentiment,
                    'score': sentiment_score,
                    'status': self.status,
                    'clicked': self.click,
                    'link': self.twitter_link
                    }
            products.insert_one(user_information)

        else:
            print("Pass")


class StdOutListener(StreamListener):

    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):

        streamer = TwitterStreamer()
        tweets = json.loads(data)
        streamer.set_data(tweets)

        return True


    def on_error(self, status):
        print(status)


if __name__ == '__main__':

    stream = TwitterStreamer()
    scrape_words = ["#flomerpresentation022020", "#flomerpresentation2020"]
    stream.auth_tweet_streamer(scrape_words)


