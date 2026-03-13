FROM python:3.11-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY minitwit_client_sim.py .

CMD [ "python", "./minitwit_client_sim.py" ]
