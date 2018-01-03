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

"""------------------------dbm setting------------------------"""

db_name = 'ncku.sqlite3'
#連結資料庫
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
#刪除資料庫的table
def delete_dvd(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dvds")
    conn.commit()
#加入檔案到資料庫
def add_dvd(conn, title, year, duration, director):
    director_id = get_and_set_director(conn, director)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO dvds "
                   "(title, year, duration, director_id) "
                   "VALUES (?, ?, ?, ?)",
                   (title, year, duration, director_id))
    conn.commit()
#get_and_set_director
def get_and_set_director(conn, director):
    director_id = get_director_id(conn, director)
    if director_id is not None:
        return director_id
    cursor = conn.cursor()
    cursor.execute("INSERT INTO directors (name) VALUES (?)",
                   (director,))
    conn.commit()
    return get_director_id(conn, director)
#get_director_id
def get_director_id(conn, director):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM directors WHERE name=?",
                   (director,))
    fields = cursor.fetchone()
    return fields[0] if fields is not None else None
#印出所有的紀錄
def all_dvds(conn,update):
    cursor = conn.cursor()
    sql = ("SELECT dvds.title, dvds.year, dvds.duration, "
           "directors.name FROM dvds, directors "
           "WHERE dvds.director_id = directors.id"
           " ORDER BY dvds.title")
    cursor.execute(sql)
    for fields in cursor:
        update.message.reply_text ([(str(fields[0]), fields[1], 'class'+str(fields[2]), str(fields[3]))])


"""------------------------set_webhook------------------------"""

app = Flask(__name__)
bot = telegram.Bot(token='499538879:AAE41TcIJOevcrxqwdfTDA5oVPTSxxWe59Q')
def _set_webhook():
    status = bot.set_webhook('https://48ab384b.ngrok.io/hook')
    if not status:
        print('Webhook setup failed')
        sys.exit(1)


"""------------------------transitions------------------------"""

states = ['no_class','class','in_class','go_home','fail','quit','pass']
transitions = [
['new_class', 'no_class', 'class'],
['sign_in', 'class', 'in_class'],
['take_a_break', 'class', 'go_home'],
['go_to_school', 'go_home', 'class'],
['leave', 'in_class', 'go_home'],
['you_quit', '*', 'quit'],
['you_fail', '*', 'fail'],
['you_pass', 'go_home', 'pass']
]

class Game(object):
	pass
life_bot = Game()
machine = Machine(model = life_bot, states = states, transitions =transitions,initial ='no_class')



"""------------------------main------------------------"""

class_num=1
class_score=0
hand_in_hk=0
@app.route('/hook', methods=['POST'])
def webhook_handler():
    if request.method == "POST":
        
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        recv=update.message.text
        global class_num
        global class_score
        global stu_num
        global hand_in_hk
        #conn = connect(db_name)

        if recv == '退選'and class_num<11:
            life_bot.you_quit()
            update.message.reply_text('退選成功')
        if recv == '寒假開始':
            life_bot.you_fail()
            update.message.reply_text('你已經死了，被當掉吧')
        if life_bot.state == 'no_class':
            stu_num=recv
            life_bot.new_class()
            text = stu_num+'確認選課，準備開始上課'+life_bot.state+str(class_num)
            update.message.reply_text(text)

        if life_bot.state == 'class':
            if recv == '簽到':
               life_bot.sign_in()
               add_dvd(conn, 'computer_theory 2017-1', 2017, class_num, stu_num)
               update.message.reply_text('上課中')
               if class_num==4:
                   update.message.reply_text('請交作業1')
                   hand_in_hk=0
               if class_num==8:
                   update.message.reply_text('請交作業1')
                   hand_in_hk=0
               if class_num==16:
                   update.message.reply_text('請交專題')
                   hand_in_hk=0
               if class_num==3:
                   update.message.reply_text('請在第四堂課交作業1')
               if class_num==7:
                   update.message.reply_text('請在第八堂課交作業1')
               if class_num==13:
                   update.message.reply_text('請在1/3號交專題')
            elif recv == '翹課':
               life_bot.take_a_break()
               if random.randint(1,2)==2:
                  update.message.reply_text('教授點名被點到')
                  class_score=class_score-5
               else:
                  update.message.reply_text('剛好沒點名')
               update.message.reply_text('又度過了美好的一天')
            elif recv != stu_num:
               update.message.reply_text('課要開始了，快走')

        if life_bot.state == 'in_class':
            if recv == '交作業'and hand_in_hk==0:
               if class_num==4:
                   update.message.reply_text('成功繳交作業1')
                   class_score=class_score+10
               if class_num==8:
                   update.message.reply_text('成功繳交作業2')
                   class_score=class_score+10
               if class_num==16:
                   update.message.reply_text('成功繳交專題')
                   class_score=class_score+10
               hand_in_hk=1
            elif recv == '回家':
               life_bot.leave()
               update.message.reply_text('又度過了美好的一天')
            elif recv == '查詢分數':
               test='現在分數'+str(class_num*6+class_score)
               update.message.reply_text(test)
            elif recv == '查詢簽到記錄':
               all_dvds(conn,update)
               update.message.reply_text('OK')
            elif recv != '簽到':
               update.message.reply_text('上課聽不懂?')

        if life_bot.state == 'go_home':
            if recv == '去上學':
               life_bot.go_to_school()
               class_num=class_num+1
               text = '準備上課'+life_bot.state+str(class_num)
               update.message.reply_text(text)
            elif class_num==18:
               class_score=class_num*6+class_score
               if(class_score>100):
                    update.message.reply_photo(499538879,photo=open('over100.jpg', 'rb'))
                    update.message.reply_text('超過一百分')
                    life_bot.you_pass()
               if(class_score<=100 and class_score>=70):
                    update.message.reply_photo(499538879,photo=open('s70~100.jpg', 'rb'))
                    update.message.reply_text('司句意！你超級棒der')
                    life_bot.you_pass()
               if(class_score<=69 and class_score>=60):
                    update.message.reply_photo(499538879,photo=open('s60~69.jpg', 'rb'))
                    update.message.reply_text('你要挺住阿！不要在混了')
                    life_bot.you_pass()
               if(class_score<=59 and class_score>=50):
                    update.message.reply_photo(499538879,photo=open('s51~59.jpg', 'rb'))
                    update.message.reply_text('真是太可惜，差一點，哈哈')
                    life_bot.you_fail()
               if(class_score<=50):
                    update.message.reply_photo(499538879,photo=open('under50.jpg', 'rb'))
                    update.message.reply_text('殘念')
                    life_bot.you_fail()
            elif recv != '回家' and recv != '翹課':
               update.message.reply_text('上課時間倒拉！')
    return 'ok'
if __name__ == "__main__":
    _set_webhook()
    conn = connect(db_name)
    delete_dvd(conn)
    app.run()
