# JobTrack

![CI](https://github.com/Tragixz/jobtrack/actions/workflows/ci.yml/badge.svg)

A REST API for tracking job applications, built with FastAPI and SQLModel.

**🔗 Live demo:** https://jobtrack-ul4b.onrender.com
*(Free hosting: the first load may take ~1 minute while the server wakes up.)*

![API docs screenshot](docs/screenshot.png)

## Features
- Create, view, update, and delete job applications
- Filter applications by status (applied, interviewing, offer, rejected, ghosted)
- Pipeline statistics, including response rate
- Follow-up reminders for applications that need a nudge
- Export to CSV
- Input validation with clear error messages

## Tech Stack
Python · FastAPI · SQLModel (SQLAlchemy + Pydantic) · SQLite · pytest · Ruff · Docker · GitHub Actions · Render

## API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| POST | `/applications` | Create an application |
| GET | `/applications?status=` | List applications, optionally filtered by status |
| GET | `/applications/{id}` | Get one application |
| PATCH | `/applications/{id}` | Update an application |
| DELETE | `/applications/{id}` | Delete an application |
| GET | `/stats` | Pipeline statistics and response rate |
| GET | `/follow-ups` | Active applications due for a follow-up |
| GET | `/export` | Download all applications as CSV |

## Running Locally
```
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```
Then open http://127.0.0.1:8000/docs

## Running Tests
```
pytest -v
```

## Running with Docker
```
docker build -t jobtrack .
docker run -p 8000:8000 jobtrack
```

## Project Structure
```
app/
  main.py       # API endpoints
  models.py     # Data models and validation
  database.py   # Database connection
tests/
  test_api.py   # Automated tests (isolated in-memory database)
.github/workflows/
  ci.yml        # Lint + test on every push
Dockerfile      # Container for deployment
```