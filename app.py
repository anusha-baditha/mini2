from flask import Flask,render_template,request,flash,redirect,url_for,session
from flask_session import Session
import flask_excel as excel  
import mysql.connector
from otp import genotp
from cmail import sendmail
from io import BytesIO
import os
import re
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
excel.init_excel(app)
Session(app)
#mydb=mysql.connector.connect(host="localhost",user="root",password="anusha@1999",db='spm')

app.secret_key='anusha@codegnan'
user=os.environ.get('RDS_USERNAME')
db=os.environ.get('RDS_DB_NAME')
password=os.environ.get('RDS_PASSWORD')
host=os.environ.get('RDS_HOSTNAME')
port=os.environ.get('RDS_PORT')
with mysql.connector.connect(host=host,port=port,user=user,password=password,db=db) as conn:
    cursor=conn.cursor()
    cursor.execute("create table if not exists  register(username varchar(50) NOT NULL,password varchar(15) DEFAULT NULL,email varchar(60) DEFAULT NULL,PRIMARY KEY (username),UNIQUE KEY email(email))")
    cursor.execute("create table if not exists notes(notes_id int NOT NULL AUTO_INCREMENT,title varchar(100) NOT NULL,content text NOT NULL,username varchar(50) NOT NULL,PRIMARY KEY (notes_id),KEY username (username),CONSTRAINT notes_ibfk_1 FOREIGN KEY (username) REFERENCES register(username))")
    cursor.execute("create table if not exists files(fid int NOT NULL AUTO_INCREMENT,extension varchar(10) DEFAULT NULL,filedata longblob,added_by varchar(50),PRIMARY KEY (fid),key added_by (added_by),CONSTRAINT files_ibfk_1 FOREIGN KEY (added_by) REFERENCES register (username))")
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db,port=port)
@app.route('/')
def index():
    return render_template('title.html')
@app.route('/registration',methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from register where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from register where email=%s',[email])
        count2=cursor.fetchone()[0]
        print(count)
        print(count2)
        if count==0:
            if count2==0:
                otp=genotp()
                subject = 'Thanks for registering'
                body = f'use this otp register {otp}'
                sendmail(email,subject,body)
                flash('The otp has sent to your mail please verify it')
                return render_template('otp.html',username=username,password=password,email=email,otp=otp)
            else:
                flash('email already existed')
                return render_template('registration.html')

        else:
            flash('username already existed')
            return render_template('registration.html')
    return render_template('registration.html')
@app.route('/otp/<username>/<password>/<email>/<otp>',methods=['GET','POST'])
def otp(username,password,email,otp):
    if request.method=='POST':
        otp1=request.form['otp']
        if otp==otp1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into register(username,password,email) values(%s,%s,%s)',[username,password,email])
            mydb.commit()
            cursor.close()
            flash('Registration successfully done')
            return redirect(url_for('login'))
        else:
            return redirect(url_for('otp'))
    return render_template('otp.html') 
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('homepage'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from register where username=%s and password=%s',[username,password])
        var1=cursor.fetchone()[0]
        cursor.close()
        if var1==1:
            session['user']=username
            return redirect(url_for('homepage'))
        else:
            return 'username or password was incorrect'
    return render_template('login.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/homepage')
def homepage():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('index'))
@app.route('/addnotes',methods=['GET','POST'])
def addnote():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            user=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notes(title,content,username) values(%s,%s,%s)',[title,content,user])
            mydb.commit()
            cursor.close()
            flash('notes has been inserted successfully')
            return redirect(url_for('homepage'))
    
    return render_template('addnotes.html')    
@app.route('/allnotes')
def allnotes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select notes_id,title from notes where username=%s',[session.get('user')])
        data=cursor.fetchall()
        cursor.close()
        return render_template('table.html',data=data)
    return redirect(url_for('login'))
@app.route('/viewnotes/<notesid>')
def viewnotes(notesid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from notes where notes_id=%s',[notesid])
        data1=cursor.fetchall()
        cursor.close()
        return render_template('viewnotes.html',data1=data1)
    return redirect(url_for('login'))
@app.route('/update/<notesid>',methods=['GET','POST'])
def update(notesid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from notes where notes_id=%s',[notesid])
        var1=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update notes set title=%s,content=%s where notes_id=%s',[title,content,notesid])
            mydb.commit()
            cursor.close()
            flash(f'notes with id {notesid} update successfully ')
            return redirect(url_for('allnotes'))


        return render_template('update.html',var1=var1)
    return redirect(url_for('login'))
@app.route('/delete/<notesid>')
def delete(notesid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where notes_id=%s',[notesid])
        mydb.commit()
        cursor.close()

        return redirect(url_for('allnotes'))
    return redirect(url_for('login'))
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        if request.method=='POST':
            name=request.form['search']
            strg=['A-Za-z0-9']
            pattern=re.compile(f'^{strg}', re.IGNORECASE)
            if (pattern.match(name)):
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select notes_id,title from notes where username=%s and title LIKE %s', [session.get('user'),name + '%'])
                data=cursor.fetchall()
                cursor.close()
                return render_template('homepage.html', items=data)
            else:
                flash('result not found')
                return redirect(url_for('homepage'))
    return redirect(url_for('login'))
@app.route('/getnotesdata')
def getdata():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        columns=['Title','Content']
        cursor.execute('select title,content from notes where username=%s',[username])
        data=cursor.fetchall()
        print(data)
        array_data=[list(i) for i in data]
        print(array_data)
        array_data.insert(0,columns)
        print(array_data)
        return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
    else:
        return redirect(url_for('login'))
@app.route('/fileup',methods=['GET','POST'])
def fileupload():
    if session.get('user'):
        if request.method=='POST':
            files=request.files.getlist('file')
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            for file in files: 
                file_ext=file.filename.split('.')[-1]
                file_data=file.read()#reads binary data from file
                cursor.execute('insert into files(extension,filedata,added_by) values(%s,%s,%s)',[file_ext,file_data,username])
                mydb.commit()
            cursor.close()
            flash('files uploded successfully')
            return redirect(url_for('homepage'))
        return render_template('fileupload.html')
    else:
        return redirect(url_for('login'))
if __name__ == '__main__':
    app.run()


