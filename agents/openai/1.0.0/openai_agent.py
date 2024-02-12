from langchain_community.tools.tavily_search import TavilySearchResults

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain.tools.retriever import create_retriever_tool
from langchain.tools import ShellTool

from langchain import hub

from langchain.agents import AgentExecutor, create_openai_functions_agent

import logging
import os

# print(f"AGENT_SETTINGS = {os.getenv('AGENT_SETTINGS')}")
# print(f"TASK_SETTINGS = {os.getenv('TASK_SETTINGS')}")

# Web search tool
# TODO: We could parameterize the max_results as a setting in TASK_SETTINGS or AGENT_SETTINGS
search_tool = TavilySearchResults(max_results=10)
logging.info(search_tool.invoke("what is the weather in SF"))

# Vector database retriever pointed at a web document or documents
# TODO: Currently unused
# TODO: list of URLs would need to be a setting in TASK_SETTINGS or AGENT_SETTINGS to make this useful
# loader = WebBaseLoader("https://docs.smith.langchain.com/overview")
# docs = loader.load()
# documents = RecursiveCharacterTextSplitter(
#     chunk_size=1000, chunk_overlap=200
# ).split_documents(docs)
# vector = FAISS.from_documents(documents, OpenAIEmbeddings())
# retriever = vector.as_retriever()
# # retriever.get_relevant_documents("how to upload a dataset")[0]
#
# retriever_tool = create_retriever_tool(
#     retriever,
#     "langsmith_search",
#     "Search for information about LangSmith. For any questions about LangSmith, you must use this tool!",
# )

# Shell tool
shell_tool = ShellTool()
shell_tool.description = shell_tool.description + f"args {shell_tool.args}".replace(
    "{", "{{"
).replace("}", "}}")
# print(shell_tool.run({"commands": ["echo 'Hello World!'", "time"]}))

# Get the prompt to use - you can modify this!
prompt = hub.pull("hwchase17/openai-functions-agent")
prompt.messages
print(prompt)

# Select the list of tools
tools = [search_tool, shell_tool]

# Pick an LLM
# TODO: Make the model name be a setting seems like a good idea
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# TODO: Add various forms of memory summarization, memory retrieval so we're not limited by the context-window size

# Make the agent
agent = create_openai_functions_agent(llm, tools, prompt)

# Make the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Set working directory to /root
os.chdir("/root")

# Get the instructions
with open("instructions.txt", "r") as instructions:
    # Run the agent executor
    agent_executor.invoke({"input": instructions.read()})
