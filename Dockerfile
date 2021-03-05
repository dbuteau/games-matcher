FROM python:alpine

ENV PATH="/opt/venv/bin/:$PATH"
RUN apk update
RUN apk add --no-cache --virtual .pynacl_deps build-base python3-dev libffi-dev
RUN python3 -m venv /opt/venv
RUN python3 -m pip install --upgrade pip
COPY bot/requirements.txt .
RUN python3 -m pip install -r requirements.txt


FROM python:alpine

COPY bot /
RUN [ -d /data ]||mkdir /data
RUN python3 -m pip install --upgrade pip
COPY --from=0 /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["python3", "app.py"]
