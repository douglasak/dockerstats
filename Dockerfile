FROM python:latest

WORKDIR /usr/src/req

#RUN apt update && apt upgrade -y

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /usr/src/app
WORKDIR /usr/src/app

ENTRYPOINT ["python3", "web.py"]