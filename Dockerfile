FROM python:3

WORKDIR /usr/src/req

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /usr/src/app
WORKDIR /usr/src/app

ENTRYPOINT ["python3", "web.py"]