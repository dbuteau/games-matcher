FROM python:alpine

ENV PATH="/opt/venv/bin/:$PATH"
RUN apk update
RUN apk add --no-cache --virtual .pynacl_deps build-base python3-dev libffi-dev
RUN python3 -m venv /opt/venv
RUN python3 -m pip install --upgrade pip
COPY bot/requirements.txt .
RUN python3 -m pip install -r requirements.txt


FROM python:alpine

ARG VCS_REF
ARG BUILD_DATE
ARG BUILD_VERSION

LABEL   org.label-schema.name="games-matcher"\
        org.label-schema.description="discord bot for helping user to find games in commons"\
        org.label-schema.url="https://github.com/dbuteau/games-matcher"\
        org.label-schema.vcs-url="https://github.com/dbuteau/games-matcher.git"\
        org.label-schema.docker.params="DISCORD_TOKEN,STEAM_API_KEY"\
        org.label-schema.build-date="$BUILD_DATE"\
        org.label-schema.vcs-ref="$VCS_REF"\
        org.label-schema.version="$BUILD_VERSION"

COPY bot /
RUN [ -d /data ]||mkdir /data
RUN python3 -m pip install --upgrade pip
COPY --from=0 /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["python3", "app.py"]
