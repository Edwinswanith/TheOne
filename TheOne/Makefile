.PHONY: up down api worker test

up:
	docker compose up -d

down:
	docker compose down

api:
	uv run uvicorn services.api.app.main:app --reload

worker:
	uv run celery -A services.worker.tasks.run_tasks.celery_app worker --loglevel=info

test:
	pytest -q

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(m)"
