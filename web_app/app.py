import os
import psycopg2
from flask import Flask, render_template

app = Flask('app.py')

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='agentplatform',
                            user='postgres',
                            password=os.environ['DB_PASSWORD'])
    return conn


# TODO: Add automatic cursor closing error handling with with or similar
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM public.agents;')
    agents = cur.fetchall()
    cur.close()
    
    cur = conn.cursor()
    cur.execute('SELECT * FROM public.tasks;')
    tasks = cur.fetchall()
    cur.close()

    conn.close()
    return render_template('index.html', agents=agents, tasks=tasks)
