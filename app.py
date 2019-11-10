
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__version__ = '1.0.0'
__author__ = 'Robert Navas, Flomer Aduna, Charlie Bautista'


from flask import Flask
from bson.objectid import ObjectId
from flask import render_template, redirect, url_for
import pymongo
import tweepy
from twitter_scraper import get_tweets
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



if __name__ == '__main__':

    app.run(debug=True, port=8080)

