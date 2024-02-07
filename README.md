# agentplatform
Platform for testing agents against tasks

# OS and Requirements
I'm not sure how much of this is specifically required, but heres the setup I developed on:
Mac OS on Apple Silicon (ARM64 M2) - I'm using Sonoma 14.2.1, but anything recent should work
Docker Desktop - I'm using version 4.23
PostgreSQL - I'm using 16.1 with pgAdmin and StackBuilder (Note: PostgreSQL is best installed on Mac using brew, the installer from EDB has useful tools like pgAdmin that work but the database itself won't install correctly.)
(I'm also using GitHub Desktop 3.3.6 and Visual Studio Code 1.85.1, but I don't think there are any dependencies on them.)

* From a design point of view, I'd expect this to be easy to port to any Linux system, and it probably could be ported to Windows without too much trouble if needed.


Sample agent tasks
1. Create a bitcoin wallet saved to a specific location
   Requirements:
   0. agent memory
   1. Find information on the web: require  websearch, e.g. in LangChain TavilySearchResults (I'll need a free API key)
   2. Download a wallet, likely a CLI one, and run it: requires CLI access, e.g. in LangChain ShellTool
  
2. Solve a UNIX crackmes
   Requirements:
   0. agent memory
   1. Find information on the web: require  websearch, e.g. in LangChain TavilySearchResults
   2. CLI reverse engineering tools. Best candidate seemes to be radare2, though it's not just a CLI but has a text-based GUI that might be hard for an agent to interface to.
   3. The crackmes to be solved, including its location and how to run it.
   4. CLI access, e.g. in LangChain ShellTool

Implementation:
Initially, Docker images. Thius should almost certainly be upraded to K8s, I may leave doing this as a TBD.
We need an agent. Langchain appears to support a number, including OpenAI tools agent and a now-deprecated OpenAI function agent both based on OpenAI, and XML Agent based on Claude. Since I have an OpenAI account, I am going with OpenAI tools agent. This will require agent memory, the default is ####

The Framework
* List of Agents (currently 1)
    * Should be versioned and/or timestamped, as we're likely to uopdate them
    * Agents could have settings or parameters
    * An agent is part of the specification of Docker/K8s image
    * Integration to a code repository such as github (or might need a local version for security)
* List of Tasks (currently 2) Each has needed extras, network security setup.
    * Again, should be versioned and/or timestamped
    * Tasks could have difficulty variants or parameters
    * A task is part of the specification of Docker/K8s image
* Combine an agent with a task to create a Docker/K8s image
    * This might be slow, and we wanted fast startup, but clealy those can be cached.
    * with 1 agent with no settings x 2 tasks with no settings, this cache is tiny, but its size could explode geometrically. Docker/K8s images are genrically large, so the amount of storage required seems challenging
    * Obvious implementation is a key-value blob store where the key is a GUID-sized hash of the agent + version + settings and task + version + settings, with a standard time-since last use caching policy
    * Needs to interface to Docker/K8s. They default to web storage, we might have security concerns with that, but could leave that as a TBD
* Need a secure means of provision of secrets such as API keys that we don't want on a web store
    * Docker Swarm provides a mechanism called Docker secrets, which sounds pretty secure
    * K8s provides Secrets. Apparently they're not very secure by default and a series of config steps are needed to make them fully secure.
    * This sounds like a good thing to leave TBD in this context.
* Set some number of these running
* Monitor them running
    * Monitor a log file - Docker and K8s support this, by logging stdout and stderr of the application to outside the container, might want convenience wrappers
        * Might also want to support looking at local log files, in which case log file paths should be part of agent/tast specifications. This seems particulalry likely for tasks, which could involve running software services for attack which might do local logging.
    * Exec into them - Docker and K8s support this, might want convenience wrappers
    * Kill the agent while leaving the image running
        * Basically just exec in and then execute an agent or agent + task specific kill command
        * Kill command seems like something for the agent/task specifications.
            * For tsks with exec access, might want a "kill everything but…" option.
    * Halt the image running - Docker and K8s support this, might want convenience wrappers
        * K8s storage is by default temporary, so is lost when the image is killed, if we want to archive this then we would need to do so explicitly
        * Docker images keep their storage until deleted
    * Human-in-the-loop was explicitly not a goal for now
        * one obvious implementation of this would be as an invisible-to-the-agent network proxy through a firewall
* Examine their output:
    * Logs - Docker and K8s support this, might want convenience wrappers
    * Exec access - Docker and K8s support this, might want convenience wrappers
    * Filesystem access - CHECK IF Docker and K8s support this, might want convenience wrappers
* Archive images
    * Compressing an image to a diff would be desirable, but leave as a TBD - CHECK IF Docker and K8s support this, might want convenience wrappers
        * container-diff lista filenames of differences between images, turning that into something that stored the actual diffs would probbaly not be too hard (images are fundamentally TAR files), so then if we had a before and afetr image we could d this. Definitely a TBD
* Delete images - Docker and K8s support this, might want convenience wrappers
* A GUI for this would be nice, but is not my forte. A web UI would seem like the obvious implementation. Docker and K8s already have app/web GUIs
We'd also need a database, and some combination of repositories for code and Docker/K8s images.

I'm not an FE developer, but I do know Javascript, and I gather node.js is widely used. there are two ways to connect ot to PostgreSQL, node-postgres and sequelize. node-postgres is oldschool, while sequelize is an ORM. Apparently they can bothe be sued in one app, so likley it's possible tom port between them, and node-postgres has a shorter learning curve.
Or if I wanted to stay in Python for each integration with ML (not obvious why this would be an advantage, apparently Django or Flask are widely used.
I'm tempted to build the DB and leave the web UI as TBD, and just build the business logic. Which I'd rather not do in Javascript, sine mine is rusty, so am leaning towards Python.

Data storage
A database would seem obvious. Data storage needs are open-ended, so one with XML or JSON sopport seems useful. I'm inclined to avoid Oracle given it's overhead. With 1 agent and 2 taks it feel like massive overkill, but obviously this is intended to scale to the point where this would be needed. I'm wondering if I should leave this as a TBD, but it feels like a large omission in a framework.
    * If we want to go NoSQL then BaseX, eXist seem like plausible candidates, but I'm not familiar with them
    * I'm inclined to just use a SQL database, this situation seems unchallenging enough for it to be a reasonable choice, in which case PostgreSQL (aka Postgres) seems like a good solution, since it supports XML and is free. (MS SQL Server does as well, but it isn't free, and I'm building on Mac, where is can only be run in a Docker container, which sounds like a pain.)
        * PostgreSQL doesn't have a built-in GUI, but some can be found at https://pgdash.io/blog/postgres-gui-tools.html

Language Choice
* One could make a security argument for using something that would be obscure enough that escaped agents would have trouble hacking into it (LISP, say), but our security should be based on things like good network firewall configs and permissions, not security-through-obscurity.
* A language that LLM researchers are likely to be familair with, and that I'm familiar with, seems like the obvious choice. So that would mean Python, or possibly C++ or Java or Javascript. For a real project there might also be an argument for doing the front-end and back-end in two different languages, especially if we had separate front-end and back-end enginenrs working on it (that might allow us to use the best tools for each job, and might encourage clean separation of concerns), but not for a quick demo prototype.
* Since I'm doing a quick demo prototype, an interpreted labgauge would be best, and I've been coding in Python for the last year or so so that's what I'm currently most in-practice in. So Python it is, front-and-back.

TODO:
1. Locate a Docker image with langchain, and set it up to run an agent with an initial prompt
2. Make the initial propmpt templated
3. Make a docker image of this
4. Make versions with needed extras preinstalled
5. Install PostgreSQL
6. Build a basic databse schema, manually or in Python
7. Get a basic web GUI up, say to read the lists of agents and tasks



    

    

   
   


