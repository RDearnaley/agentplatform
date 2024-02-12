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


# TODO: Add a form to the web app and make it run the agent/task build commands as needed, with appropriate path and settings values templated in.
# TODO: This needs to have a way of spinning up multiple copies of the agent+task in parallel, under Docker or K8s
# TODO: A case could be made that the following code should live in a separate file
# TODO: The following code is untested


# cd up to the agentplatform directory
def _cd_up():
    while not os.getcwd().endswith("/agentplatform"):
        os.chdir(os.getcwd() + "/..")


# Build the base Docker image
def build_docker_base():
    _cd_up()
    os.system("docker pull langchain/langchain")
    os.chdir(os.getcwd() + "/docker/base")
    os.system('docker build -t "agentplatform/base:Dockerfile" .')
    _cd_up()
    os.chdir(os.getcwd() + "/web_app")


# Build the agent Docker image
def build_docker_agent(agent_path, agent_version, settings):
    _cd_up()
    os.chdir(os.getcwd() + f"/agents/{agent_path}/{agent_version}")
    os.system(
        f'docker build -f Dockerfile.agent --build-arg settings="{settings}" -t "agentplatform/{agent_path}/{agent_version}:Dockerfile" --pull=false .'
    )
    _cd_up()
    os.chdir(os.getcwd() + "/web_app")


# Build the task Docker image
def task(agent_path, agent_version, task_path, task_version, settings):
    _cd_up()
    os.chdir(os.getcwd() + f"/tasks/{task_path}/{task_version}")
    os.system(
        f'docker build -f Dockerfile.task --build-arg agent_path="{agent_path}/{agent_version}" --build-arg settings="{settings}" -t "agentplatform/{agent_path}/{agent_version}/{task_path}/{task_version}:Dockerfile/" --pull=false .'
    )
    _cd_up()
    os.chdir(os.getcwd() + "/web_app")
