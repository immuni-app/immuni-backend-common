FROM python:3.8-buster AS build

WORKDIR /app
ENV VIRTUAL_ENV /app/.venv
ENV POETRY_HOME /app/.poetry
ENV POETRY_VERSION 1.1.4
ENV PATH $POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH
# Prometheus requires this envar name for multiprocess, and it has to be an absolute path.
ENV prometheus_multiproc_dir /app/.prometheus/multiproc

COPY entrypoint.sh entrypoint.sh

RUN mkdir -p $prometheus_multiproc_dir \
    && python3 -m venv $VIRTUAL_ENV

# CI requirement to run poetry install.
ARG HTTP_PROXY
ARG HTTPS_PROXY

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/${POETRY_VERSION}/get-poetry.py | python \
    && poetry config virtualenvs.in-project true

COPY poetry.lock pyproject.toml ./

# The common submodule.
COPY common common

# The microservice to build.
ARG SERVICE_DIR
COPY $SERVICE_DIR $SERVICE_DIR

# NOTE: to perform security scans, generate requirements.txt.
RUN poetry install \
    --no-dev \
    --no-root \
    && poetry export -f requirements.txt > requirements.txt

################################
# Api
################################

FROM python:3.8-slim-buster AS api

WORKDIR /app
ENV PYTHONPATH /app
ENV VIRTUAL_ENV /app/.venv
ENV POETRY_HOME /app/.poetry
ENV PATH $POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH
# Prometheus requires this envar name for multiprocess, and it has to be an absolute path.
ENV prometheus_multiproc_dir /app/.prometheus/multiproc

COPY --from=build /app /app

# Openshift requires the user group to be root.
RUN useradd \
        --no-log-init \
        --home /app \
        --shell /bin/bash \
        immuni \
    && chown \
        --recursive \
        immuni:root \
        /app \
    && chmod -R g+rwx /app
USER immuni

ARG API_PORT
ENV API_PORT $API_PORT
EXPOSE $API_PORT/tcp

# Build info for monitoring purposes, exposed to the running application.
ARG GIT_BRANCH
ARG GIT_SHA
ARG GIT_TAG
ARG BUILD_DATE
ENV GIT_BRANCH $GIT_BRANCH
ENV GIT_SHA $GIT_SHA
ENV GIT_TAG $GIT_TAG
ENV BUILD_DATE $BUILD_DATE

ENTRYPOINT ["./entrypoint.sh", "api"]
CMD []

################################
# Worker
################################

FROM python:3.8-slim-buster AS worker

WORKDIR /app
ENV PYTHONPATH /app
ENV VIRTUAL_ENV /app/.venv
ENV POETRY_HOME /app/.poetry
ENV PATH $POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH
# Prometheus requires this envar name for multiprocess, and it has to be an absolute path.
ENV prometheus_multiproc_dir /app/.prometheus/multiproc

COPY --from=build /app /app

# Openshift requires the user group to be root.
RUN useradd \
        --no-log-init \
        --home /app \
        --shell /bin/bash \
        immuni \
    && chown \
        --recursive \
        immuni:root \
        /app \
    && chmod -R g+rwx /app
USER immuni

# Build info for monitoring purposes, exposed to the running application.
ARG GIT_BRANCH
ARG GIT_SHA
ARG GIT_TAG
ARG BUILD_DATE
ENV GIT_BRANCH $GIT_BRANCH
ENV GIT_SHA $GIT_SHA
ENV GIT_TAG $GIT_TAG
ENV BUILD_DATE $BUILD_DATE

ENTRYPOINT ["./entrypoint.sh", "worker"]
CMD []

################################
# Beat
################################

FROM python:3.8-slim-buster AS beat

ENV PYTHONPATH /app
ENV VIRTUAL_ENV /app/.venv
ENV POETRY_HOME /app/.poetry
ENV PATH $POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH
# Prometheus requires this envar name for multiprocess, and it has to be an absolute path.
ENV prometheus_multiproc_dir /app/.prometheus/multiproc

WORKDIR /app

COPY --from=build /app /app

# Running after the copy to avoid caching of this layer in case of code changes.
# The proxy is a CI requirement to run apt.
# procps is needed to perform the healthcheck on the beat container.
RUN echo "Acquire::http::Proxy \"$HTTP_PROXY\";" > /etc/apt/apt.conf.d/proxy.conf \
    && apt-get update \
    && apt-get install -y procps

# Openshift requires the user group to be root.
RUN useradd \
        --no-log-init \
        --home /app \
        --shell /bin/bash \
        immuni \
    && chown \
        --recursive \
        immuni:root \
        /app \
    && chmod -R g+rwx /app
USER immuni

# Build info for monitoring purposes, exposed to the running application.
ARG GIT_BRANCH
ARG GIT_SHA
ARG GIT_TAG
ARG BUILD_DATE
ENV GIT_BRANCH $GIT_BRANCH
ENV GIT_SHA $GIT_SHA
ENV GIT_TAG $GIT_TAG
ENV BUILD_DATE $BUILD_DATE

ENTRYPOINT ["./entrypoint.sh", "beat"]
CMD []
