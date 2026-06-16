from typing import Any
from google import genai
from app.core.config import settings

_client = genai.Client(api_key=settings.GEMINI_API_KEY)


def _llm_call(system_prompt: str, user_content: str) -> str:
    combined = f"{system_prompt}\n\n{user_content}"
    response = _client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=combined,
    )
    return response.text or ""


def financial_agent(context_chunks: list[str], company_name: str) -> dict[str, Any]:
    context = "\n\n".join(context_chunks[:12])
    system = (
        "You are an expert financial analyst specializing in due diligence. "
        "Analyze the provided document excerpts and return a structured JSON with keys: "
        "revenue_growth, gross_margin, operating_margin, net_income, free_cash_flow, pe_ratio, summary."
    )
    user = f"Company: {company_name}\n\nDocument Excerpts:\n{context}"
    raw = _llm_call(system, user)
    return {"agent": "financial", "raw": raw}


def risk_agent(context_chunks: list[str], company_name: str) -> dict[str, Any]:
    context = "\n\n".join(context_chunks[:12])
    system = (
        "You are a risk assessment specialist. Analyze the document excerpts for risk factors. "
        "Return a structured JSON with keys: regulatory_risk, litigation_risk, market_risk, "
        "operational_risk, overall_risk_level (Low/Medium/High), key_risks (list), summary."
    )
    user = f"Company: {company_name}\n\nDocument Excerpts:\n{context}"
    raw = _llm_call(system, user)
    return {"agent": "risk", "raw": raw}


def market_agent(context_chunks: list[str], company_name: str) -> dict[str, Any]:
    context = "\n\n".join(context_chunks[:12])
    system = (
        "You are a market intelligence analyst. Analyze the document excerpts. "
        "Return a structured JSON with keys: market_share, tam, sam, competitors (list), "
        "competitive_advantages (list), market_trends (list), summary."
    )
    user = f"Company: {company_name}\n\nDocument Excerpts:\n{context}"
    raw = _llm_call(system, user)
    return {"agent": "market", "raw": raw}


def investment_thesis_agent(
    financial_result: dict,
    risk_result: dict,
    market_result: dict,
    company_name: str,
) -> dict[str, Any]:
    system = (
        "You are a senior investment analyst. Based on the financial, risk, and market analyses, "
        "synthesize a comprehensive investment thesis. "
        "Return a JSON with keys: recommendation (Buy/Hold/Sell), conviction (High/Medium/Low), "
        "price_target, bull_case, bear_case, key_catalysts (list), thesis_summary."
    )
    user = (
        f"Company: {company_name}\n\n"
        f"Financial Analysis: {financial_result.get('raw', '')}\n\n"
        f"Risk Analysis: {risk_result.get('raw', '')}\n\n"
        f"Market Analysis: {market_result.get('raw', '')}"
    )
    raw = _llm_call(system, user)
    return {"agent": "thesis", "raw": raw}


def report_generator_agent(
    company_name: str,
    financial_result: dict,
    risk_result: dict,
    market_result: dict,
    thesis_result: dict,
) -> dict[str, Any]:
    system = (
        "You are a professional investment report writer. "
        "Compile all agent findings into a structured executive summary report. "
        "Format: Executive Summary, Financial Overview, Risk Assessment, "
        "Market Position, Investment Thesis, Conclusion."
    )
    user = (
        f"Company: {company_name}\n\n"
        f"Financial: {financial_result.get('raw', '')}\n\n"
        f"Risk: {risk_result.get('raw', '')}\n\n"
        f"Market: {market_result.get('raw', '')}\n\n"
        f"Thesis: {thesis_result.get('raw', '')}"
    )
    report_text = _llm_call(system, user)
    return {"agent": "report_generator", "report": report_text}
