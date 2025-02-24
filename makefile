create-db:
	python3 create_db.py

start-server:
	python3 manage.py runserver

migrate:
	python3 manage.py migrate

make-migration:
	python3 manage.py makemigrations

install-requirements:
	pip3 install -r requirements.txt

update-requirements:
	pip3 freeze > requirements.txt

new-admin:
	python3 manage.py createsuperuser

new-app:
	python3 manage.py startapp $(name)

compose-up:
	docker compose up

compose-down:
	docker compose down

