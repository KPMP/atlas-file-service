FROM python:3.7.12-alpine3.14
WORKDIR /code
ENV FLASK_APP app.py
ENV FLASK_RUN_HOST 0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers tzdata
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install -U flask-cors
CMD ["flask", "run"]