#=================flask code starts here
from flask import Flask, render_template, request, redirect, url_for, session,send_from_directory
import os
from werkzeug.utils import secure_filename
from distutils.log import debug
from fileinput import filename
from werkzeug.utils import secure_filename
import sqlite3
import pickle
import random

import smtplib 
from email.message import EmailMessage
from datetime import datetime

#importing all required python libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GridSearchCV
from catboost import CatBoostClassifier
from sklearn import metrics 
import seaborn as sns
import matplotlib.pyplot as plt #use to visualize dataset values
import os

UPLOAD_FOLDER = os.path.join('static', 'uploads')
# Define allowed files
ALLOWED_EXTENSIONS = {'csv'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'welcome'

#loading and displaying hospital stay icu dataset
dataset = pd.read_csv("Dataset/LengthOfStay.csv", nrows=2000)

#dataset pre-processing like converting non-numeric data to numeric data using label encoder class
dataset['vdate'] = pd.to_datetime(dataset['vdate'])
dataset['year'] = dataset['vdate'].dt.year
dataset['month'] = dataset['vdate'].dt.month
dataset['day'] = dataset['vdate'].dt.day
label_encoder = []
columns = dataset.columns
types = dataset.dtypes.values
for i in range(len(types)):
    name = types[i]
    if name == 'object': #finding column with object type
        le = LabelEncoder()
        dataset[columns[i]] = pd.Series(le.fit_transform(dataset[columns[i]].astype(str)))#encode all str columns to numeric
        label_encoder.append([columns[i], le])
Y = dataset['lengthofstay'].ravel()
dataset.drop(['eid', 'vdate','lengthofstay'], axis = 1,inplace=True)#drop ir-relevant columns
print("Cleaned & Processed Dataset")

#applying imputation to replace missing values with mean
dataset = dataset.fillna(dataset.mean())
columns = dataset.columns
X = dataset.values
#normalizing training features
scaler = MinMaxScaler()
X = scaler.fit_transform(X)
print("Normalized Training Features = "+str(X))

#split dataset into train and test
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2)
print("Dataset Train & Test Split Details")

#training CatBoost algorithm on tuning parameters
extension_model = CatBoostClassifier(iterations = 20)
#training CatBoost algorithm on training features
extension_model.fit(X_train, y_train)
#perform prediction on test data
predict = extension_model.predict(X_test)

labels = ['Short Stay', 'Long Stay']

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/notebook')
def notebook():
    return render_template('ICUStayPrediction.html')


@app.route('/PredictAction', methods=['GET', 'POST'])
def PredictAction():

    if request.method == 'POST':
        f = request.files.get('file')
        data_filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],data_filename))
        session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'],data_filename)
        data_file_path = session.get('uploaded_data_file_path', None)
        testData = pd.read_csv(data_file_path)
        data = testData.values
        testData['vdate'] = pd.to_datetime(testData['vdate'])#convert date into numeric date format
        testData['year'] = testData['vdate'].dt.year
        testData['month'] = testData['vdate'].dt.month
        testData['day'] = testData['vdate'].dt.day
        for i in range(len(label_encoder)):#convert string data to numeric values
            le = label_encoder[i]
            testData[le[0]] = pd.Series(le[1].transform(testData[le[0]].astype(str)))#encode all str columns to numeric
        testData.drop(['eid', 'vdate'], axis = 1,inplace=True)#drop ir-relevant columns
        #handling missing values using imputation
        testData = testData.fillna(dataset.mean())
        testData = testData.values
        testData = scaler.transform(testData)#normalize test data
        predict = extension_model.predict(testData)#perform prediction on test data using extension model
        output = ""
        for i in range(len(predict)):
            output += "Test Data = "+str(data[i])+" Predicted ICU Stay ====> "+labels[predict[i]]+"<br/><br/>" 
        return render_template('result.html', msg=output)

@app.route('/logon')
def logon():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('signin.html')

@app.route("/signup")
def signup():
    global otp, username, name, email, number, password
    username = request.args.get('user','')
    name = request.args.get('name','')
    email = request.args.get('email','')
    number = request.args.get('mobile','')
    password = request.args.get('password','')
    otp = random.randint(1000,5000)
    print(otp)
    msg = EmailMessage()
    msg.set_content("Your OTP is : "+str(otp))
    msg['Subject'] = 'OTP'
    msg['From'] = "vandhanatruprojects@gmail.com"
    msg['To'] = email
    
    
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("vandhanatruprojects@gmail.com", "pahksvxachlnoopc")
    s.send_message(msg)
    s.quit()
    return render_template("val.html")

@app.route('/predict_lo', methods=['POST'])
def predict_lo():
    global otp, username, name, email, number, password
    if request.method == 'POST':
        message = request.form['message']
        print(message)
        if int(message) == otp:
            print("TRUE")
            con = sqlite3.connect('signup.db')
            cur = con.cursor()
            cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",(username,email,password,number,name))
            con.commit()
            con.close()
            return render_template("signin.html")
    return render_template("signup.html")

@app.route("/signin")
def signin():

    mail1 = request.args.get('user','')
    password1 = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?",(mail1,password1,))
    data = cur.fetchone()

    if data == None:
        return render_template("signin.html")    

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("home.html")
    else:
        return render_template("signin.html")


    
if __name__ == '__main__':
    app.run()