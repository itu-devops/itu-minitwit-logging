FROM python:3

EXPOSE 5000

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY minitwit_client_sim.py .

CMD [ "python", "./minitwit_client_sim.py" ]
