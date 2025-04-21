#!/bin/bash

echo "resetting db"

echo "yes" | pipenv run python manage.py flush
rm ./maritimeapp/migrations/*
pipenv run python manage.py makemigrations maritimeapp
pipenv run python manage.py migrate maritimeapp --fake
rm -fr ./src/
rm -fr ./src_csvs/
echo "starting scripts"
pipenv run python manage.py import_dd 
pipenv run python manage.py psql_add
pipenv run python manage.py update_dates
echo "done"
