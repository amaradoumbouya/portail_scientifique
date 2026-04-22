FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

COPY . /app

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
