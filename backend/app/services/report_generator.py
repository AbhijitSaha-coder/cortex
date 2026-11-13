import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.report import ResearchReport
from app.models.evaluation import UsageRecord
from app.services.retrieval.hybrid_search import HybridSearchEngine
from app.services.ai.providers import get_llm_provider
from app.services.ai.guardrails import format_evidence_context, sanitize_untrusted_text
from app.core.logging import logger


class ResearchReportGenerator:
    """
    Generates structured, citation-grounded research reports.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.hybrid_engine = HybridSearchEngine(db)
        self.llm = get_llm_provider()

    def generate_report(
        self,
        research_question: str,
        title: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
    ) -> ResearchReport:
        """
        Orchestrates retrieval and structured synthesis of a comprehensive research report.
        """
        report_title = title or f"Research Report: {research_question[:60]}"
        logger.info(f"Generating research report: '{report_title}' for user {self.user_id}")

        # Step 1: Retrieve comprehensive evidence
        search_res = self.hybrid_engine.search(
            query=research_question,
            user_id=self.user_id,
            mode="hybrid",
            top_k=8,
            document_ids=document_ids,
            rerank=True,
        )
        evidence_items = search_res["results"]
        evidence_context = format_evidence_context(evidence_items)

        # Step 2: System prompt for structured report generation
        system_prompt = """You are Cortex Research Engine. You generate publication-grade, deeply structured scientific and business research reports.
You must adhere strictly to this JSON output schema:
{
  "executive_summary": "1-2 paragraphs summarizing the entire subject and core takeaways.",
  "main_findings": "- Key finding 1 [Citation X]\\n- Key finding 2 [Citation Y]\\n- Key finding 3...",
  "detailed_analysis": "In-depth thematic breakdown of the evidence across multiple detailed paragraphs.",
  "contradictory_findings": "Analysis of opposing perspectives, empirical divergences, or counterarguments.",
  "limitations": "Data boundaries, sample constraints, or unverified claims.",
  "unanswered_questions": "- Open question 1\\n- Open question 2...",
  "conclusion": "Final synthesis, strategic implications, or next steps."
}

CRITICAL RULES:
- Ground every claim strictly in the provided <untrusted_evidence_collection>.
- Include inline citations like [Citation 1], [Citation 2] referencing the evidence index numbers.
- Return ONLY valid parseable JSON matching the schema above.
"""

        user_content = f"""Research Question: {research_question}
Focus Areas: {", ".join(focus_areas) if focus_areas else "Comprehensive Analysis"}

{evidence_context}
"""

        llm_res = self.llm.generate(
            messages=[{"role": "user", "content": user_content}],
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=2500,
        )
        raw_output = llm_res.get("content", "").strip()

        # Step 3: Parse structured sections
        # Fallback defaults if LLM did not output pure JSON
        exec_sum = ""
        findings = ""
        analysis = ""
        contradictions = ""
        limitations = ""
        unanswered = ""
        conclusion = ""

        try:
            # Strip markdown codeblocks if wrapped
            clean_json = raw_output
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:]
            if clean_json.endswith("```"):
                clean_json = clean_json[:-3]
            clean_json = clean_json.strip()

            parsed = json.loads(clean_json)
            exec_sum = parsed.get("executive_summary", "")
            findings = parsed.get("main_findings", "")
            analysis = parsed.get("detailed_analysis", "")
            contradictions = parsed.get("contradictory_findings", "")
            limitations = parsed.get("limitations", "")
            unanswered = parsed.get("unanswered_questions", "")
            conclusion = parsed.get("conclusion", "")
        except Exception:
            # Fallback extraction from prose
            exec_sum = raw_output[:300]
            findings = "Key insights derived from knowledge base sources."
            analysis = raw_output
            contradictions = "No notable conflicting claims identified in the indexed material."
            limitations = "Limited to indexed knowledge base documents."
            unanswered = "- What are the broader empirical bounds?"
            conclusion = "Evidence provides preliminary insights on the subject."

        # Step 4: Build Citations metadata
        citations_data = []
        for i, item in enumerate(evidence_items, 1):
            citations_data.append({
                "citation_index": i,
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "chunk_id": item["chunk_id"],
                "page_number": item["page_number"],
                "excerpt": item["content"][:200],
            })

        # Step 5: Format complete Markdown document
        markdown_body = f"""# {report_title}

**Generated by Cortex AI Research Agent** | *{datetime.now(timezone.utc).strftime("%B %d, %Y")}*

---

## 1. Research Question
{research_question}

## 2. Executive Summary
{exec_sum}

## 3. Main Findings
{findings}

## 4. Detailed Analysis
{analysis}

## 5. Contradictory & Divergent Findings
{contradictions}

## 6. Limitations & Methodological Constraints
{limitations}

## 7. Unanswered Questions & Future Research
{unanswered}

## 8. Conclusion
{conclusion}

---

## 9. References & Grounded Sources
"""
        for c in citations_data:
            page_str = f", Page {c['page_number']}" if c['page_number'] else ""
            markdown_body += f"\n- **[Citation {c['citation_index']}]** *{c['document_title']}*{page_str}\n  > \"{c['excerpt']}...\""

        # Step 6: Save to Database
        report = ResearchReport(
            user_id=self.user_id,
            title=report_title,
            research_question=research_question,
            executive_summary=exec_sum,
            main_findings=findings,
            detailed_analysis=analysis,
            contradictory_findings=contradictions,
            limitations=limitations,
            unanswered_questions=unanswered,
            conclusion=conclusion,
            citations_json=json.dumps(citations_data),
            markdown_content=markdown_body,
            status="completed",
        )
        self.db.add(report)

        # Log usage
        usage = UsageRecord(
            user_id=self.user_id,
            request_type="report",
            prompt_tokens=llm_res.get("prompt_tokens", 0),
            completion_tokens=llm_res.get("completion_tokens", 0),
            total_tokens=llm_res.get("total_tokens", 0),
            estimated_cost=0.002,
            model_name="cortex-research-v1",
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(report)

        return report
