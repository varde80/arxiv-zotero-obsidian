"""LLM-based paper summarizer using Claude API."""

import os
from dataclasses import dataclass
from typing import List, Optional

import anthropic


@dataclass
class PaperSummary:
    """Structured summary of a paper."""

    summary: str
    key_findings: List[str]
    methodology: str
    contributions: str
    limitations: str
    future_work: str


class PaperSummarizer:
    """Summarize academic papers using Claude API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """Initialize the summarizer.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
            model: Claude model to use.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def summarize(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        language: str = "ko",
    ) -> PaperSummary:
        """Generate a structured summary of a paper.

        Args:
            title: Paper title.
            authors: List of author names.
            abstract: Paper abstract.
            language: Output language ('ko' for Korean, 'en' for English).

        Returns:
            PaperSummary with structured summary fields.
        """
        lang_instruction = "한국어로" if language == "ko" else "in English"

        prompt = f"""다음 학술 논문의 정보를 바탕으로 {lang_instruction} 요약해주세요.

## 논문 정보
- 제목: {title}
- 저자: {', '.join(authors)}
- 초록: {abstract}

## 요청 형식
다음 각 섹션을 작성해주세요:

1. **요약** (3-5문장): 논문의 핵심 내용을 간결하게 설명
2. **핵심 발견** (3-5개 항목): 가장 중요한 발견/결과를 bullet point로
3. **방법론** (2-3문장): 사용된 연구 방법 설명
4. **주요 기여** (2-3문장): 이 논문의 학술적 기여
5. **한계점** (1-2문장): 논문의 한계나 제약사항
6. **향후 연구** (1-2문장): 제안된 후속 연구 방향

## 출력 형식 (정확히 이 형식으로 출력):
[SUMMARY]
요약 내용

[KEY_FINDINGS]
- 발견 1
- 발견 2
- 발견 3

[METHODOLOGY]
방법론 설명

[CONTRIBUTIONS]
주요 기여 설명

[LIMITATIONS]
한계점 설명

[FUTURE_WORK]
향후 연구 방향"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        return self._parse_response(response_text)

    def _parse_response(self, response: str) -> PaperSummary:
        """Parse the structured response into a PaperSummary object."""
        sections = {
            "summary": "",
            "key_findings": [],
            "methodology": "",
            "contributions": "",
            "limitations": "",
            "future_work": "",
        }

        current_section = None
        current_content = []

        for line in response.split("\n"):
            line = line.strip()

            if line.startswith("[SUMMARY]"):
                current_section = "summary"
                current_content = []
            elif line.startswith("[KEY_FINDINGS]"):
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "key_findings"
                current_content = []
            elif line.startswith("[METHODOLOGY]"):
                if current_section == "key_findings":
                    sections["key_findings"] = [
                        item.lstrip("- ").strip()
                        for item in current_content
                        if item.strip().startswith("-")
                    ]
                elif current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "methodology"
                current_content = []
            elif line.startswith("[CONTRIBUTIONS]"):
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "contributions"
                current_content = []
            elif line.startswith("[LIMITATIONS]"):
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "limitations"
                current_content = []
            elif line.startswith("[FUTURE_WORK]"):
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "future_work"
                current_content = []
            elif current_section and line:
                current_content.append(line)

        # Handle last section
        if current_section and current_content:
            if current_section == "key_findings":
                sections["key_findings"] = [
                    item.lstrip("- ").strip()
                    for item in current_content
                    if item.strip().startswith("-") or item.strip()
                ]
                # Clean up non-bullet items
                sections["key_findings"] = [
                    item for item in sections["key_findings"] if item
                ]
            else:
                sections[current_section] = "\n".join(current_content).strip()

        return PaperSummary(
            summary=sections["summary"],
            key_findings=sections["key_findings"] if sections["key_findings"] else [],
            methodology=sections["methodology"],
            contributions=sections["contributions"],
            limitations=sections["limitations"],
            future_work=sections["future_work"],
        )
