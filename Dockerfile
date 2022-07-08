FROM python:3.9
COPY . .
RUN pip3 config set global.index-url https://pypi.douban.com/simple
RUN pip3 install -r requirements.txt

CMD python server.py

