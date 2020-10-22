FROM python:3.7-slim-buster

COPY bot /

RUN python3 -m ensurepip --default-pip
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install discord.py
RUN python3 -m pip install SQLAlchemy

ENTRYPOINT ["python3", "app.py"]