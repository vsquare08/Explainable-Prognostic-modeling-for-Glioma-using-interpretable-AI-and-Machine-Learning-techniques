from flask import Flask, render_template, redirect, request, url_for
import mysql.connector
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3307",
    database='glioma'
)

mycursor = mydb.cursor()

def executionquery(query, values):
    mycursor.execute(query, values)
    mydb.commit()

def retrivequery1(query, values):
    mycursor.execute(query, values)
    return mycursor.fetchall()

def retrivequery2(query):
    mycursor.execute(query)
    return mycursor.fetchall()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = [i[0] for i in email_data]
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
                values = (name, email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID already exists!")
        return render_template('register.html', message="Confirm password does not match!")
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = [i[0] for i in email_data]

        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password_data = retrivequery1(query, values)
            if password.upper() == password_data[0][0]:
                global user_email
                user_email = email
                return redirect("/home")
            return render_template('login.html', message="Invalid Password!")
        return render_template('login.html', message="This email ID does not exist!")
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    prediction = None
    if request.method == 'POST':
        input_data = {
            'Gender': int(request.form['Gender']),
            'Age_at_diagnosis': float(request.form['Age_at_diagnosis']),
            'Race': int(request.form['Race']),
            'IDH1': int(request.form['IDH1']),
            'TP53': int(request.form['TP53']),
            'ATRX': int(request.form['ATRX']),
            'PTEN': int(request.form['PTEN']),
            'EGFR': int(request.form['EGFR']),
            'CIC': int(request.form['CIC']),
            'MUC16': int(request.form['MUC16']),
            'PIK3CA': int(request.form['PIK3CA']),
            'NF1': int(request.form['NF1']),
            'PIK3R1': int(request.form['PIK3R1']),
            'FUBP1': int(request.form['FUBP1']),
            'RB1': int(request.form['RB1']),
            'NOTCH1': int(request.form['NOTCH1']),
            'BCOR': int(request.form['BCOR']),
            'CSMD3': int(request.form['CSMD3']),
            'SMARCA4': int(request.form['SMARCA4']),
            'GRIN2A': int(request.form['GRIN2A']),
            'IDH2': int(request.form['IDH2']),
            'FAT4': int(request.form['FAT4']),
            'PDGFRA': int(request.form['PDGFRA'])
        }

        single_input_df = pd.DataFrame([input_data])

        scaler = joblib.load('scaler.joblib')
        model = joblib.load('Random Forest_best_model.pkl')

        single_input_scaled = scaler.transform(single_input_df)

        prediction = model.predict(single_input_scaled)
        result = prediction[0]
        if result==0:
            prediction="LGG"
        else:
            prediction="GBM"

    df = pd.read_csv("TCGA_GBM_LGG_Mutations_all.csv")
    columns_to_drop = ['Grade', 'Project', 'Case_ID', 'Primary_Diagnosis', 'Age_at_diagnosis']
    df = df.drop(columns=columns_to_drop)
    df.columns = [col.replace(' ', '_') for col in df.columns]
    object_columns = df.select_dtypes(include=['object']).columns
    labels = {col: df[col].value_counts().to_dict() for col in object_columns}
    le = LabelEncoder()
    encodes = {}
    for col in object_columns:
        df[col] = le.fit_transform(df[col])
        encodes[col] = df[col].value_counts().to_dict()
    dic = {key: [(sub_key, id_key) for sub_key, value in labels[key].items() for id_key, id_value in encodes[key].items() if value == id_value] for key in labels.keys()}
    return render_template('prediction.html', data=dic, prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
