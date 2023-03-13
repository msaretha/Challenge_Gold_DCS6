import re
import pandas as pd
import sqlite3 as sql3

from flask import Flask, jsonify, request
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from

app = Flask(__name__)

app.json_encoder = LazyJSONEncoder
# app.json = LazyJSONEncoder
swagger_template = dict(
info = {
    'title': LazyString(lambda:'Documentation Data Processing and Modeling'),
    'version' : LazyString(lambda: '1.0.0'),
    'description' : LazyString(lambda: 'API documentation explains the available endpoints and provides example data and result along with document  descriptions'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json'
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app,template = swagger_template, config = swagger_config)
@swag_from("docs/text_processing.yml", methods=['POST'])
@app.route('/text-processing', methods=['POST'])
def text_processing():
    teks_input = request.form.get('text')
    teks_output = cleansing(teks_input)
     
    json_respon = {
        'input' : teks_input,
        'output' : teks_output,
    }
    response_data = jsonify(json_respon)
   
    return response_data

@swag_from("docs/file_processing.yml", methods=['POST'])
@app.route('/file-processing', methods=['POST'])
def file_processing():
    file = request.files["file"]
    df_csv = pd.read_csv(file, encoding="latin-1")
    df_csv = df_csv['Tweet']
    df_csv = df_csv.drop_duplicates()
    # df_csv['New_Tweet'] = df_csv['Tweet'].apply(cleansing)

    df_csv = df_csv.values.tolist()
    ix = 0
    datanya = {}
    for str in df_csv:
        datanya[ix] = {}
        datanya[ix]['tweet'] = str
        datanya[ix]['new_tweet'] = cleansing(str)
        ix = ix + 1
    # return_file = {
    #     'output' : df_csv
    # }
    return datanya

    # return df_csv

# proses ambil data di database ke dataframe
conn = sql3.connect("abusive_text.db", check_same_thread=False)

def removeVowels(str):
    vowels = 'aeiou'
    for ele in vowels:
        str = str.replace(ele, 'x')
    return str

def case_folding(teks):
    # proses cleansing
    # 1. jadikan teks agar lowercase
    teks = teks.lower()
    # 2. hanya menerima alfabet text
    teks = re.sub(r"[^\w\d\s]+", " ",teks)
    # menghapus whitespace di awal dan di akhir kalimat
    teks = teks.strip()
    return teks

# ubah kata alay menjadi kata baku
def normalization_alay(teks):
    df_alay = pd.read_sql_query('select * from ALAY', conn)
    dict_alay = dict(zip(df_alay['teks_alay'],df_alay['teks_baku']))
    teks = teks.split()
    teks_normal = ''
    for str in teks:
        if(bool(str in dict_alay)):
            teks_normal = teks_normal + ' ' + dict_alay[str]
        else:
            teks_normal = teks_normal + ' ' + str
    teks_normal = teks_normal.strip()
    return teks_normal

# fungsi untuk sensor kata-kata abusive
def normalization_abusive(teks):
    df_abusive = pd.read_sql_query("select * from ABUSIVE", conn)
    dict_abusive = dict(zip(df_abusive['teks'],df_abusive['teks']))
    teks = teks.split()
    teks_normal = ''
    for str in teks:
        if(bool(str in dict_abusive)):
            str = removeVowels(str)
            teks_normal = teks_normal + ' ' + str
        else:
            teks_normal = teks_normal + ' ' + str  
    teks_normal = teks_normal.strip()
    return teks_normal
   
def cleansing(teks):
    teks = case_folding(teks)
    teks = normalization_alay(teks)
    teks = normalization_abusive(teks)
    
    return teks

if __name__ == '__main__' :
    app.run(debug=True)


