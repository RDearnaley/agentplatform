FROM langchain/langchain AS agentplatform_base
COPY requirements.txt /etc/requirements.txt
RUN python3 -m pip install -r /etc/requirements.txt
CMD sleep 60