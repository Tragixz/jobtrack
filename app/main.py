import csv
import io
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, col, select

from app.database import create_db, get_session
from app.models import (
    Application,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    Status,
)

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db()
    yield


app = FastAPI(
    title="JobTrack",
    description="An API for tracking jobs",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


def get_or_404(session: Session, application_id: int) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return application





@app.post("/applications", response_model=ApplicationRead, status_code=201)
def create_application(data: ApplicationCreate, session: SessionDep):
    application = Application.model_validate(data)
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


@app.get("/applications", response_model=list[ApplicationRead])
def list_applications(session: SessionDep, status: Status | None = None):
    query = select(Application)
    if status is not None:
        query = query.where(Application.status == status)
    query = query.order_by(col(Application.applied_on).desc())
    return session.exec(query).all()


@app.get(
    "/applications/{application_id}",
    response_model=ApplicationRead,
)
def get_application(application_id: int, session: SessionDep):
    return get_or_404(session, application_id)


@app.patch("/applications/{application_id}", response_model=ApplicationRead)
def update_application(application_id: int, data: ApplicationUpdate, session: SessionDep):
    application = get_or_404(session, application_id)
    application.sqlmodel_update(data.model_dump(exclude_unset=True))
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


@app.delete("/applications/{application_id}", status_code=204)
def delete_application(application_id: int, session: SessionDep):
    application = get_or_404(session, application_id)
    session.delete(application)
    session.commit()


@app.get("/stats")
def get_stats(session: SessionDep):
    applications = session.exec(select(Application)).all()
    counts = {s.value: 0 for s in Status}
    for application in applications:
        counts[Status(application.status).value] += 1

    total = len(applications)
    responded = total - counts["applied"] - counts["ghosted"]
    response_rate = round(responded / total * 100, 1) if total else 0.0
    return {"total": total, "by_status": counts, "response_rate": response_rate}


@app.get("/follow-ups", response_model=list[ApplicationRead])
def get_follow_ups(session: SessionDep):
    """Applications that are still active and due for a follow-up."""
    query = (
        select(Application)
        .where(col(Application.follow_up_on) <= date.today())
        .where(col(Application.status).in_([Status.applied, Status.interviewing]))
    )
    return session.exec(query).all()


@app.get("/export")
def export_csv(session: SessionDep):
    applications = session.exec(select(Application)).all()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(ApplicationRead.model_fields))
    writer.writeheader()
    for application in applications:
        writer.writerow(application.model_dump(mode="json"))
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )
