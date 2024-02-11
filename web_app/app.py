import os
import psycopg2
from flask import Flask, render_template

app = Flask("app.py")


def get_db_connection():
    connection = psycopg2.connect(
        host="localhost",
        database="agentplatform",
        user="postgres",
        password=os.environ["DB_PASSWORD"],
    )
    return connection


# TODO: We should have Python data classes called Agent and Task, with named member
# variables, and setter functions where there are contraints to satisfy, and set up
# psycopg2's adaptor mechanism (see:
# https://www.psycopg.org/docs/advanced.html#type-casting-of-sql-types-into-python-objects
# ) for automatic type conversion to these, rather than just accessing these as
# unprotected arrays

@app.route("/")
def index():
    try:
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM public.agents;")
            agents = cursor.fetchall()
        finally:
            cursor.close()

        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM public.tasks;")
            tasks = cursor.fetchall()
        finally:
            cursor.close()

    finally:
        connection.close()

    return render_template("index.html", agents=agents, tasks=tasks)
