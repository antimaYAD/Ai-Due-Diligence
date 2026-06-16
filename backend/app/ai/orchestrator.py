from typing import Any
from sqlalchemy.orm import Session

from app.ai.agents import (
    financial_agent,
    risk_agent,
    market_agent,
    investment_thesis_agent,
    report_generator_agent,
)
from app.ai.rag import retrieve_chunks


def run_agent_pipeline(
    company_id: str,
    analysis_type: str,
    db: Session,
) -> dict[str, Any]:
    from app.models.company import Company

    company = db.query(Company).filter(Company.id == company_id).first()
    company_name = company.name if company else "Unknown Company"

    chunks = retrieve_chunks(
        query=f"{company_name} financial performance risk market",
        company_id=company_id,
        top_k=20,
    )
    context_chunks = [c["content"] for c in chunks]

    financial_result = financial_agent(context_chunks, company_name)
    risk_result = risk_agent(context_chunks, company_name)
    market_result = market_agent(context_chunks, company_name)

    thesis_result = investment_thesis_agent(
        financial_result, risk_result, market_result, company_name
    )

    report_result = report_generator_agent(
        company_name, financial_result, risk_result, market_result, thesis_result
    )

    return {
        "data": {
            "financial": financial_result,
            "risk": risk_result,
            "market": market_result,
            "thesis": thesis_result,
        },
        "summary": report_result.get("report", ""),
    }
