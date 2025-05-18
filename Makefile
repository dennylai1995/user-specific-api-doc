.PHONY: demo-run-frontend
demo-run-frontend:
	python3 -m http.server

.PHONY: demo-run-backend
demo-run-backend:
	cd backend && python3 main.py