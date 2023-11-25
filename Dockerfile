FROM python:3.10-alpine

# prevent Python from writing .pyc files 禁止寫入.pyc檔案
ENV PYTHONDONTWRITEBYCODE 1
# ensure Python output is sent directly to the terminal without buffering 直接發送至終端不進行緩衝
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install --upgrade pip
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY ./db.sqlite3 /user/src/app/db.sqlite3

COPY . /app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]