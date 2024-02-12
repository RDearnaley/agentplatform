# agentplatform
Platform for testing agents against tasks

Tasks I skipped for this demo are marked 'TODO' or 'TBD'


## OS and Requirements
I'm not sure how much of this is specifically required, but heres the setup I developed on:
Mac OS on Apple Silicon (ARM64 M2) - I'm using Sonoma 14.2.1, but anything recent should work
Docker Desktop - I'm using version 4.23
PostgreSQL - I'm using 16.1 with pgAdmin and StackBuilder (Note: PostgreSQL is best installed on Mac using brew, the installer from EDB has useful tools like pgAdmin that work but the database itself won't install correctly.):

brew update
brew doctor
brew install postgres

If you installed PostgreSQL with brew then the command to start the database cluster running (if you don't have it set up to start automatically) should be something like:

/opt/homebrew/bin/postgres -D /opt/homebrew/var/postgresql@14

or:

brew services start postgresql@14

#### Installation output
PostgreSQL user: username: postgres password: xyccok-duHzes-8rydsi [TODO: In a production system this would be stored securely encrpted at rest]
This formula has created a default database cluster with:
  initdb --locale=C -E UTF-8 /opt/homebrew/var/postgresql@14
For more details, read:
  https://www.postgresql.org/docs/14/app-initdb.html

To start postgresql@14 now and restart at login:
  brew services start postgresql@14

(I'm also using GitHub Desktop 3.3.6 and Visual Studio Code 1.85.1, but I don't think there are any dependencies on them.)

I'm using conda for python library version control. To do the same you will need to install it, set current working directory to the agentplatform directory, then run the following:

./scripts/conda_init_.zsh                           [run once, creates the conda environment]
conda activate agentplatform                        [run in each shell]
./scripts/requirements.zsh                          [run once, pip installs requirements.txt into the environment]

TODO: I also provided the conda activate agentplatform command as a script ./scripts/conda.zsh but somehow it doesn't seem to function correctly when run in a script (probably it needs access to the base shell).

To set up the database schema (if you're not just pointing to the one in agentplatform/PostgreSQL/14/data/), create a user called postgres, a tablespace called agentplatform, a database called agentplatform, and then run:

export DB_PASSWORD=" xyccok-duHzes-8rydsi "         [password for postgres user of agentplatform/PostgreSQL/14/data/, update this if you created your own user]
python3 ./web_app/init_db.py

TODO: In a non-demo system the database user password would NOT be in the README.md, it would be in a proper secret store, encrypted at rest, and we'd have a script to load it from there into the environment variable.


## Design Discussion

- From a design point of view, I'd expect this to be easy to port to any Linux system, and it probably could be ported to Windows without too much trouble if needed.

### Sample agent tasks
1. Create a bitcoin wallet saved to a specific location
   Requirements:
   0. agent memory
   1. Find information on the web: require  websearch, e.g. in LangChain TavilySearchResults (I'll need a free API key)
   2. Download a wallet tool, likely a CLI one, and run it: requires CLI access, e.g. in LangChain ShellTool
  
2. Solve a UNIX crackmes
   Requirements:
   0. agent memory
   1. Find information on the web: require  websearch, e.g. in LangChain TavilySearchResults
   2. CLI reverse engineering tools. Best candidate seems to be radare2, though it's not just a CLI but has a text-based GUI that might be hard for an agent to interface to.
   3. The crackmes to be solved, including its location and how to run it.
   4. CLI access, e.g. in LangChain ShellTool

#### Implementation:
Initially, Docker images. This should almost certainly be upgraded to K8s, I may leave doing this as a TBD.
We need an agent. Langchain appears to support a number, including OpenAI tools agent and a now-deprecated OpenAI function agent both based on OpenAI, and XML Agent based on Claude. Since I have an OpenAI account, I am going with OpenAI tools agent. This will require agent memory, the default is (TBD).

### The Framework

- List of Agents (currently 1)
    - Should be versioned and/or timestamped, as we're likely to update them
    - Agents could have settings or parameters
    - An agent is part of the specification of Docker/K8s image
    - Integration to a code repository such as github (or might need a local version for security)
- List of Tasks (currently 2) Each has needed extras, network security setup.
    - Again, should be versioned and/or timestamped
    - Tasks could have difficulty variants or parameters
    - A task is part of the specification of Docker/K8s image
- Combine an agent with a task to create a Docker/K8s image
    - This might be slow, and we wanted fast startup, but clealy those can be cached.
    - with 1 agent with no settings x 2 tasks with no settings, this cache is tiny, but its size could explode geometrically. Docker/K8s images are generically large, so the amount of storage required seems challenging (currently 1.2 GB/image]
    - Obvious implementation is a key-value blob store where the key is a GUID-sized hash of the agent + version + settings and task + version + settings, with a standard time-since last use caching policy
    - Needs to interface to Docker/K8s. They default to web storage, we might have security concerns with that, but could leave that as a TBD
- Need a secure means of provision of secrets such as API keys that we don't want on disk
    - Docker Swarm provides a mechanism called Docker secrets, which sounds pretty secure
    - K8s provides Secrets. Apparently they're not very secure by default and a series of config steps are needed to make them fully secure.
    - This sounds like a good thing to leave TODO in this context.
- Set some number of these running
- Monitor them running
    - Monitor a log file - Docker and K8s support this, by logging stdout and stderr of the application to outside the container, TODO might want convenience wrappers
        - Might also want to support looking at local log files, in which case log file paths should be part of agent/task specifications. This seems particularly likely for tasks, which could involve running software services for attack which might do local logging.
    - Exec into them - Docker and K8s support this, TODO might want convenience wrappers
    - Kill the agent while leaving the image running
        - Basically just exec in and then execute an agent or agent + task specific kill command
        - Kill command seems like something for the agent/task specifications.
            - For tsks with exec access, might want a "kill everything but…" option.
    - Halt the image running - Docker and K8s support this, TODO might want convenience wrappers
        - K8s storage is by default temporary, so is lost when the image is killed, if we want to archive this then we would need to do so explicitly
        - Docker images keep their storage until deleted
    - Human-in-the-loop was explicitly not a goal for now
        - one obvious implementation of this would be as an invisible-to-the-agent network proxy through a firewall
- Examine their output:
    - Logs - Docker and K8s support this, TODO might want convenience wrappers
    - Exec access - Docker and K8s support this, TODO might want convenience wrappers
    - Filesystem access - CHECK IF Docker and K8s support this, TODO might want convenience wrappers
- Archive images
    - Compressing an image to a diff would be desirable, but leave as a TODO - CHECK IF K8s supports this, might want convenience wrappers
        - From messages I'm getting from Docker on memory saved when I delete images, it looks like it does this automatically, so we don't need to implement it - nice!
        - container-diff list filenames of differences between images, turning that into something that stored the actual diffs would probbaly not be too hard (images are fundamentally TAR files), so then if we had a before and after image we could d this. Definitely a TBD
- Delete images - Docker and K8s support this, TODO might want convenience wrappers
- A GUI for this would be nice, but is not my forte. A web UI would seem like the obvious implementation. Docker and K8s already have app/web GUIs
We'd also need a database, and some combination of repositories for code and Docker/K8s images.

I'm not an FE developer, but I do know Javascript, and I gather node.js is widely used. There are two ways to connect it to PostgreSQL, node-postgres and sequelize. node-postgres is oldschool, while sequelize is an ORM. Apparently they can both be used in one app, so likely it's possible to port between them, and node-postgres has a shorter learning curve.
Or if I wanted to stay in Python for easier integration with ML (not clear why this would be an advantage), apparently Django or Flask are widely used. Django is better for larger projects, but has a longer learning curve
    - For this quick demo, I'll use Flask. For a real project, Django would probably be a better choice.
I'm tempted to build the DB and leave the web UI as TBD, and just build the business logic. Which I'd rather not do in Javascript, since mine is rusty, so I am leaning towards Python.

#### Data storage
A database would seem obvious. Data storage needs are open-ended, so one with XML or JSON support seems useful. I'm inclined to avoid Oracle given it's overhead. With 1 agent and 2 tasks it feel like massive overkill, but obviously this is intended to scale to the point where this would be needed. I'm wondering if I should leave this as a TBD, but it feels like a large omission in a framework.
    - If we want to go NoSQL then BaseX, eXist seem like plausible candidates, but I'm not familiar with them
    - I'm inclined to just use a SQL database, this situation seems unchallenging enough for it to be a reasonable choice, in which case PostgreSQL (aka Postgres) seems like a good solution, since it supports XML and is free. (MS SQL Server does as well, but it isn't free, and I'm building on Mac, where is can only be run in a Docker container, which sounds like a pain.)
        - PostgreSQL doesn't have a built-in GUI, but some can be found at https://pgdash.io/blog/postgres-gui-tools.html

- Currently the parameters XML blob is just a column in agent and task tables, so we don't easily support running the same agent or task with different parameter settings (you have to duplicate the entire agent or task to then alter the parameters do so). Very likely this should be made into two hierarchies, one for agents and one for tasks, where you select an agent/task then select one of the corresponding sets of settings.

#### Language Choice
- One could make a security argument for using something that would be obscure enough that escaped agents would have trouble hacking into it (LISP, say), but our security should be based primarily on things like good network firewall configs and permissions, not security-through-obscurity.
- A language that LLM researchers are likely to be familiar with, and that I'm familiar with, seems like the obvious choice. So that would mean Python, or possibly C++ or Java or Javascript. For a real project there might also be an argument for doing the front-end and back-end in two different languages, especially if we had separate front-end and back-end enginenrs working on it (that might allow us to use the best tools for each job, and might encourage clean separation of concerns), but not for a quick demo prototype.
- Since I'm doing a quick demo prototype, an interpreted language would be best, and I've been coding in Python for the last year or so so that's what I'm currently most in-practice in. So Python it is, front-and-back.
    - Therefore of Django or Flask, as stated above Flask makes more sense for a quick demo.
    - Connecting Flask to PostgreSQL the standard approach is to use psycopg2.

## TODO:
1. Make the agent's initial prompt templated
2. Make task versions with needed extras preinstalled
3. Improve the web app to include a select-to-build-and-run form
4. Add a hash-based Docker image cache mechanism, if Docker doesn't already have one?
5. Handle task-specific network security settings: this should probably be handled in Kubernetes, so will likely leave is as a TODO


## Use Instructions

### Running the Web App

TODO: For a production app we should use a real WSGI web server rather than a Flask development environment (which is what the script starts)

Make sure you have run the export DB_PASSWORD=... command given above, and your current working directory is the agentplatform directory, then run:

./scripts/web_app.zsh

Then point your browser to http://127.0.0.1:5000/ to see the proof-of-concept web app.

TODO: Make a proper well-designed and elegant web app, with a good UX for all needed functionality, not a quick hack proof-of-concept

### Docker Build Commands

TODO: Add a form to the web app and make it run the agent/task build commands as needed, with appropriate path and settings values templated in.
This needs to have a way of spinning up multiple copies of the agent+task in parallel, under Docker or K8s
Functions for doing the builds are sketched out (untested) in web_app/app.py

Build Base:

docker pull langchain/langchain
cd docker/base
docker build -t "agentplatform/base:Dockerfile" .
cd ../..

Build Agent:

(Template settings "<settings>foo</settings>" and agent path "agents/openai/1.0.0")

cd agents/openai/1.0.0/
docker build -f Dockerfile.agent --build-arg settings="<settings>foo</settings>" -t "agentplatform/agents/openai/1.0.0:Dockerfile" --pull=false .
cd ../..

Build Task:

(Template settings <settings>bar</settings>", agent path "agents/openai/1.0.0", and task path "tasks/reverse_engineering/crackmes/1.0.0")

cd tasks/reverse_engineering/crackmes/1.0.0
docker build -f Dockerfile.task --build-arg agent_path="agents/openai/1.0.0" --build-arg settings="<settings>bar</settings>" -t "agentplatform/agents/openai/1.0.0/tasks/reverse_engineering/crackmes/1.0.0:Dockerfile/" --pull=false .
cd ../../../..

or:

cd tasks/unix_cli/create_bitcoin_wallet/1.0.0
docker build -f Dockerfile.task --build-arg agent_path="agents/openai/1.0.0" --build-arg settings="<settings>bar</settings>" -t "agentplatform/agents/openai/1.0.0/tasks/unix_cli/create_bitcoin_wallet/1.0.0:Dockerfile/" --pull=false .
cd ../../../..


## Notes

On the Bitcoin wallet task, probably since the agent is running as root, ~ is undefined, so I altered the task to writing to /root/wallet.json and helpfully set the cwd to /root for it.
With few helpful hints it got as far as starting to downloading a Bitcoin wallet app that has a CLI, then ran out of context length due to lengthy output spooling from the download process.
TODO We need to give the agent a sliding window context that keeps the initial instructions in context with summarization of what was elided. langchain seem to have various tools like this, but since you said not to work on agent capabilities I've left this as a TODO.