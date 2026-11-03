from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
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

@app.get("/applications/{application_id}", response_model=ApplicationRead)
def get_application(application_id: int, session: SessionDep):
    return get_or_404(session, application_id)


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
        query = query.filter(Application.status == status)
        query = query.order_by(col(Application.applied_on).desc())
        return session.exec(query).all()

@app.get("/applications/{application_id}",
response_model=ApplicationRead,)
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



