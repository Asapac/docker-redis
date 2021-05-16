FROM python:3.6.3-slim
COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY ./app.py /app.py
#EXPOSE 80
#CMD [ "python", "/app.py" ]
#CMD ["/usr/local/bin/gunicorn", "--workers=2", "-b 0.0.0.0:8000","app:app"]