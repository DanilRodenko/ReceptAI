FROM ubuntu:latest
LABEL authors="abcd"

ENTRYPOINT ["top", "-b"]