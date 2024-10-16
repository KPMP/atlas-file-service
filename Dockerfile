FROM python:3.7.12-alpine3.14
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN apk add --no-cache gcc musl-dev linux-headers tzdata libffi-dev libc-dev
COPY app.py app.py
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install -U flask-cors
CMD ["gunicorn", "-b", ":5000", "app:app"]