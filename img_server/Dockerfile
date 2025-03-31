FROM python:3.11-slim-buster

WORKDIR /img_server

COPY . .
RUN pip install diffusers transformers flask torch gunicorn

CMD ["gunicorn", "-b" , "0.0.0.0:5500", "app:app", "--workers=1"]
