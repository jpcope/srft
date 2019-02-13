FROM python:3.6.5-slim-jessie

ARG S6_VERSION=v1.21.4.0
ENV S6_VERSION=$S6_VERSION

# install build utilities
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y \
    make \
    git \
    ssh \
    curl \
    tar \
    netcat

# install s6
RUN curl -SsL https://github.com/just-containers/s6-overlay/releases/download/${S6_VERSION}/s6-overlay-amd64.tar.gz | tar xvz -C /

RUN pip install pip==18.0

RUN pip install pipenv==2018.7.1

# set location of virtualenv files to <project>/.venv/
ENV PIPENV_VENV_IN_PROJECT=1

# prevent python from buffering stdout/stdin by default
ENV PYTHONUNBUFFERED=1

# install prebuilt libraries required for python modules
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get install -y \
    build-essential

# configure WORKDIR
WORKDIR /opt/service

COPY ./Pipfile* ./
RUN pipenv run python -m pip install pip==18.0 \
    && ( test ! -f Pipfile.lock || pipenv sync ) \
    && ( test -f Pipfile.lock || pipenv install )

# Install more dependencies via:
# pipenv run pipenv install <dependency_name[==version]>

# configure s6
COPY ./docker/root/ /

COPY ./ ./

CMD ["/init"]
