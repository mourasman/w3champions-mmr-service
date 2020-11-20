FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

WORKDIR /w3champions-mmr-service

COPY . .

RUN pip install pipenv
RUN pipenv install

CMD pipenv run python main.py
