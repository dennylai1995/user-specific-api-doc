FROM ubuntu:20.04

# Add Tini
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

RUN \
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y python3-pip && \
    apt-get install -y net-tools && \
    pip3 install fastapi==0.78.0 uvicorn==0.18.2 passlib==1.7.4 pydantic==1.9.0 python-jose==3.3.0 python-multipart==0.0.5

RUN mkdir -p /home/customAPI

COPY ./static /home/customAPI/static
COPY ./auth.py /home/customAPI/auth.py
COPY ./endpoint.py /home/customAPI/endpoint.py
COPY ./__init__.py /home/customAPI/__init__.py
COPY ./main.py /home/customAPI/main.py

WORKDIR "/home/customAPI"

ENTRYPOINT ["/tini", "--"]
CMD ["python3", "main.py"]