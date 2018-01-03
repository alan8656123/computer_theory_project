import sys
import telegram
import random
import json
import fileinput
import dbm
import os
import sqlite3
from flask import Flask, request
from transitions import State
from transitions.extensions import GraphMachine as Machine

db_name = 'ncku.sqlite3'

def connect(name):
    create = not os.path.exists(name)
    conn = sqlite3.connect(name)
    if create:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE directors ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, "
            "name TEXT UNIQUE NOT NULL)")
        cursor.execute("CREATE TABLE dvds ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, "
            "title TEXT NOT NULL, "
            "year INTEGER NOT NULL, "
            "duration INTEGER NOT NULL, "
            "director_id INTEGER NOT NULL, "
            "FOREIGN KEY (director_id) REFERENCES directors)")
        conn.commit()

    return conn

def add_dvd(conn, title, year, duration, director):
    director_id = get_and_set_director(conn, director)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO dvds "
                   "(title, year, duration, director_id) "
                   "VALUES (?, ?, ?, ?)",
                   (title, year, duration, director_id))
    conn.commit()

def get_and_set_director(conn, director):
    director_id = get_director_id(conn, director)
    if director_id is not None:
        return director_id
    cursor = conn.cursor()
    cursor.execute("INSERT INTO directors (name) VALUES (?)",
                   (director,))
    conn.commit()
    return get_director_id(conn, director)

def get_director_id(conn, director):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM directors WHERE name=?",
                   (director,))
    fields = cursor.fetchone()
    return fields[0] if fields is not None else None

def all_dvds(conn):
    cursor = conn.cursor()
    sql = ("SELECT dvds.title, dvds.year, dvds.duration, "
           "directors.name FROM dvds, directors "
           "WHERE dvds.director_id = directors.id"
           " ORDER BY dvds.title")
    cursor.execute(sql)
    return [(str(fields[0]), fields[1], fields[2], str(fields[3]))
            for fields in cursor]

def all_directors(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM directors ORDER BY name")
    return [str(fields[0]) for fields in cursor]

app = Flask(__name__)
bot = telegram.Bot(token='499538879:AAE41TcIJOevcrxqwdfTDA5oVPTSxxWe59Q')
def _set_webhook():
    status = bot.set_webhook('https://7aa0af24.ngrok.io/hook')
    if not status:
        print('Webhook setup failed')
        sys.exit(1)




states = ['no_class','class','in_class','go_home']
transitions = [
['new_class', 'no_class', 'class'],
['sign_in', 'class', 'in_class'],
['take_a_break', 'class', 'go_home'],
['go_to_school', 'go_home', 'class'],
['leave', 'in_class', 'go_home']
]

class Game(object):
	pass
life_bot = Game()
machine = Machine(model = life_bot, states = states, transitions =transitions,initial ='no_class')






class_num=1
class_score=0
@app.route('/hook', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        recv=update.message.text
        global class_num
        global class_score
        #conn = connect(db_name)
        if life_bot.state == 'no_class':
            if recv == '開始上課':
               life_bot.new_class()
               text = '準備上課'+life_bot.state+str(class_num)
               update.message.reply_text(text)
            else:
               update.message.reply_text('你沒事不去上學是要在家裡耍廢逆')

        if life_bot.state == 'class':
            if recv == '簽到':
               life_bot.sign_in()
               add_dvd(conn, 'computer_theory 2017', 2018, 1, 'F74041080')
               print(all_dvds(conn))
               update.message.reply_text('上課中')
            elif recv == '翹課':
               life_bot.take_a_break()
               print(all_directors(conn))
               if random.randint(1,2)==2:
                  update.message.reply_text('教授點名被點到')
                  class_score=class_score-5
               else:
                  update.message.reply_text('剛好沒點名')
               update.message.reply_text('又度過了美好的一天')
            elif recv != '開始上課':
               update.message.reply_text('課要開始了，快走')

        if life_bot.state == 'in_class':
            if recv == '回家':
               life_bot.leave()
               update.message.reply_text('回家假奔')
               update.message.reply_text('又度過了美好的一天')
            elif recv == '查詢分數':
               test='現在分數'+str(class_num*6+class_score)
               update.message.reply_text(test)
            elif recv != '簽到':
               update.message.reply_text('上課聽不懂?')

        if life_bot.state == 'go_home':
            if recv == '去上學':
               life_bot.go_to_school()
               class_num=class_num+1
               text = '準備上課'+life_bot.state+str(class_num)
               update.message.reply_text('還想繼續睡?')
               update.message.reply_text(text)
            elif class_num==18:
               class_score=class_num*6+class_score
               if(class_score>100):
                    update.message.reply_photo(499538879,photo=open('over100.jpg', 'rb'))
                    update.message.reply_text('end！')
            elif recv != '回家' and recv != '翹課':
               update.message.reply_text('上課時間倒拉！')
    return 'ok'
if __name__ == "__main__":
    _set_webhook()
    conn = connect(db_name)
    app.run()
