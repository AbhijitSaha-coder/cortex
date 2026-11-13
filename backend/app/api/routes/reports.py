import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.report import ResearchReport
from app.schemas.report import ReportGenerateRequest, ReportResponse, ReportExportResponse
from app.services.report_generator import ResearchReportGenerator

router = APIRouter(prefix="/reports", tags=["Research Reports"])


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a structured, citation-grounded research report.
    """
    generator = ResearchReportGenerator(db, current_user.id)
    report = generator.generate_report(
        research_question=payload.research_question,
        title=payload.title,
        focus_areas=payload.focus_areas,
        document_ids=payload.document_ids,
    )
    
    citations = json.loads(report.citations_json) if report.citations_json else []
    return ReportResponse(
        id=report.id,
        title=report.title,
        research_question=report.research_question,
        executive_summary=report.executive_summary,
        main_findings=report.main_findings,
        detailed_analysis=report.detailed_analysis,
        contradictory_findings=report.contradictory_findings,
        limitations=report.limitations,
        unanswered_questions=report.unanswered_questions,
        conclusion=report.conclusion,
        markdown_content=report.markdown_content,
        citations=citations,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("", response_model=List[ReportResponse])
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists research reports belonging to the authenticated user."""
    reports = (
        db.query(ResearchReport)
        .filter(ResearchReport.user_id == current_user.id)
        .order_by(ResearchReport.created_at.desc())
        .all()
    )
    res = []
    for r in reports:
        citations = json.loads(r.citations_json) if r.citations_json else []
        res.append(
            ReportResponse(
                id=r.id,
                title=r.title,
                research_question=r.research_question,
                executive_summary=r.executive_summary,
                main_findings=r.main_findings,
                detailed_analysis=r.detailed_analysis,
                contradictory_findings=r.contradictory_findings,
                limitations=r.limitations,
                unanswered_questions=r.unanswered_questions,
                conclusion=r.conclusion,
                markdown_content=r.markdown_content,
                citations=citations,
                status=r.status,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )
    return res


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves full details of a specific research report."""
    r = (
        db.query(ResearchReport)
        .filter(ResearchReport.id == report_id, ResearchReport.user_id == current_user.id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    citations = json.loads(r.citations_json) if r.citations_json else []
    return ReportResponse(
        id=r.id,
        title=r.title,
        research_question=r.research_question,
        executive_summary=r.executive_summary,
        main_findings=r.main_findings,
        detailed_analysis=r.detailed_analysis,
        contradictory_findings=r.contradictory_findings,
        limitations=r.limitations,
        unanswered_questions=r.unanswered_questions,
        conclusion=r.conclusion,
        markdown_content=r.markdown_content,
        citations=citations,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a research report."""
    r = (
        db.query(ResearchReport)
        .filter(ResearchReport.id == report_id, ResearchReport.user_id == current_user.id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    db.delete(r)
    db.commit()
    return None


@router.get("/{report_id}/export")
def export_report_markdown(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports the report as a downloadable Markdown (.md) document."""
    r = (
        db.query(ResearchReport)
        .filter(ResearchReport.id == report_id, ResearchReport.user_id == current_user.id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    safe_title = "".join(c for c in r.title if c.isalnum() or c in ("-", "_")).rstrip()
    filename = f"{safe_title}.md"

    return Response(
        content=r.markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

