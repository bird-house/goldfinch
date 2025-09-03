FROM python:3.12-slim
LABEL description.short="Goldfinch processes for climate analysis."
LABEL description.long="Docker image employed by goldfinch climate processes defined through CWL for portability."
LABEL maintainer="Francis Charette-Migneault <francis.charette-migneault@crim.ca>"
LABEL vendor="CRIM"
LABEL version="0.1.0"

COPY src/ ./src/
COPY Makefile pyproject.toml ./
RUN apt-get update && \
    apt-get -y install git make && \
    make install && \
    rm Makefile pyproject.toml && \
    apt-get remove -y build-essential make git && \
    apt autoremove -y

# should be overridden by the invoked CWL process
ENTRYPOINT ["bash"]
