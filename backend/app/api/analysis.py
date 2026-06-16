import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.analysis import Analysis, Report
from app.models.user import User
from app.schemas.analysis import AnalysisRequest, AnalysisOut, ReportOut
from app.worker.tasks import run_analysis

router = APIRouter(prefix="/analysis", tags=["Analysis"])

VALID_TYPES = {"financial", "risk", "market", "thesis", "full"}


@router.post("/", response_model=AnalysisOut, status_code=status.HTTP_201_CREATED)
def create_analysis(
    payload: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.analysis_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid analysis type. Must be one of: {VALID_TYPES}")

    analysis = Analysis(
        id=str(uuid.uuid4()),
        company_id=payload.company_id,
        analysis_type=payload.analysis_type,
        status="pending",
        requested_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    run_analysis.delay(analysis_id=analysis.id)

    return analysis


@router.get("/", response_model=list[AnalysisOut])
def list_analyses(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Analysis)
    if company_id:
        query = query.filter(Analysis.company_id == company_id)
    return query.order_by(Analysis.created_at.desc()).all()


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/reports/", response_model=list[ReportOut])
def list_reports(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Report)
    if company_id:
        query = query.filter(Report.company_id == company_id)
    return query.order_by(Report.created_at.desc()).all()


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
