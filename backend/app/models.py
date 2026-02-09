from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class TemplateType(str, Enum):
    OWN_FUNDS_CR1 = "own_funds_cr1"
    CAPITAL_REQUIREMENTS_CR2 = "capital_requirements_cr2"


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about regulatory reporting")
    scenario: Optional[str] = Field(None, description="Description of the reporting scenario")
    template_type: TemplateType = Field(default=TemplateType.OWN_FUNDS_CR1)


class RegulatoryReference(BaseModel):
    document: str
    section: str
    paragraph: str
    content: str
    relevance_score: float


class TemplateField(BaseModel):
    field_id: str
    field_name: str
    value: Optional[Any]
    justification: str
    regulatory_references: List[str]
    confidence_score: float


class ValidationIssue(BaseModel):
    severity: str  # error, warning, info
    field_id: Optional[str]
    message: str
    rule: str


class AuditLogEntry(BaseModel):
    timestamp: datetime
    field_id: str
    regulatory_reference: str
    justification: str


class TemplateOutput(BaseModel):
    template_type: TemplateType
    fields: List[TemplateField]
    validation_issues: List[ValidationIssue]
    audit_log: List[AuditLogEntry]
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    query: str
    scenario: Optional[str]
    regulatory_references: List[RegulatoryReference]
    template_output: TemplateOutput
    processing_time_seconds: float
    llm_model: str
