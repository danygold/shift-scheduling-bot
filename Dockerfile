FROM python:3.10

RUN useradd -m shiftuser

USER shiftuser

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD python /app/main.py