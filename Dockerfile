FROM python:3.7-alpine
ADD . /code
WORKDIR /code

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD ["-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]