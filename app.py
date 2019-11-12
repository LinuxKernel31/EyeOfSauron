
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__version__ = '1.0.0'
__author__ = 'Robert Navas, Flomer Aduna, Charlie Bautista'


from flask import Flask
from bson.objectid import ObjectId
from twitter_scraper import get_tweets
from flask import Flask
from flask import render_template
from flask import request
from flask import *
from random import sample
import random
from datetime import datetime
import time
from bs4 import BeautifulSoup
import urllib3 as url
import certifi as cert
import tweepy
from textblob import TextBlob
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import json
import pymongo
import re

app = Flask(__name__)


DB_HOST = 'ds259347.mlab.com'
DB_PORT = 59347
DB_USER = 'admin'
DB_PASS = 'admin123'
DB_NAME = 'heroku_d78xw6lj'

myclient = pymongo.MongoClient(DB_HOST, DB_PORT, retryWrites= False)
mydb = myclient[DB_NAME]
mydb.authenticate(DB_USER, DB_PASS)

products = mydb['products']
reserve = mydb['reserved']
count = mydb['count']


@app.route('/', methods= ['GET', 'POST'])
def index():

    users = list(map(lambda x: x, products.find()))
    return render_template('index.html', user= users)

@app.route('/realtimetweets', methods= ['GET', 'POST'])
def realtimetweets():

    users = list(map(lambda x: x, products.find()))
    return render_template('realtimetweets.html', user=users)

@app.route('/selected/<id>', methods=['GET', 'POST'])
def selected(id):

    screen_name = ''
    location= ''
    sentence= ''
    sentiment= ''
    score= ''
    status= ''
    link = ''
    for text in products.find({"_id": ObjectId(id)}):

        screen_name = text['screen_name']
        location = text['location']
        sentence = text['text']
        sentiment = text['sentiment']
        score = text['score']
        status = True
        link = text['link']
        
    reserve.insert_one({"screen_name" : screen_name,
                        "location": location,
                        "sentence": sentence,
                        "sentiment": sentiment,
                        "score" : score,
                        "status" : status,
                        "link": link})    

    query = {"_id" : ObjectId(id)}
    products.delete_one(query)

    return redirect(url_for('addclients'))

@app.route('/addclients', methods= ['GET', 'POST'])
def addclients():

    users = list(map(lambda x: x, reserve.find()))
    return render_template('selected.html', users= users)


@app.route('/deleteclients/<id>', methods= ['GET', 'POST'])
def deleteclients(id):

    query = {"_id" : ObjectId(id)}
    reserve.delete_one(query)
    users = list(map(lambda x: x, reserve.find()))

    return render_template('selected.html', users= users)


@app.route('/scout', methods=['GET', 'POST'])
def scout():

    return render_template('scout.html')

@app.route('/company/<company_name>', methods=['GET', 'POST'])
def company(company_name):
    data = []
    sentence = ''
    for tweets in get_tweets(company_name, pages=1):
        sentence = tweets['text']
        sentence = re.sub('(http\S+|@\S+|#\S+|[^\x00-\x7F ]+|[^a-zA-Z.\d\s])', '' , sentence)
        data.append(sentence)


    return render_template('company.html', name= company_name,  datas= data)

@app.route('/datavis', methods=['GET', 'POST'])
def datavis():

    return render_template('datavis.html')

@app.route('/chart-data', methods= ['GET', 'POST'])
def chart_data():
    def get_stock_price():


     
        while True:

            positive_count = count.find_one({'pos': {'$exists': True}})['pos']
            negative_count = count.find_one({'neg': {'$exists': True}})['neg']
            neutral_count = count.find_one({'neu': {'$exists': True}})['neu']

            # http = url.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=cert.where())
            # html_doc = http.request('GET', 'https://finance.yahoo.com/quote/' + name + '?p=' + name)
            # soup = BeautifulSoup(html_doc.data, 'html.parser')
            # ratbu = soup.find("span", class_="Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)").text
            # ratbu = ratbu.replace(',', '')
            json_data = json.dumps(
                {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'positive': positive_count, 'negative': negative_count, 'neutral': neutral_count })
            yield f"data:{json_data}\n\n"

            time.sleep(5)
               


    return Response(get_stock_price(), mimetype='text/event-stream')

if __name__ == '__main__':

    app.run(debug=True, port=8080)

