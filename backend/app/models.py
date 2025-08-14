from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ContractStatus(BaseModel):
    contract_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    error: Optional[str] = None

class PartyInfo(BaseModel):
    name: str
    legal_entity: Optional[str] = None
    registration_details: Optional[str] = None
    signatories: List[str] = []
    roles: List[str] = []

class AccountInfo(BaseModel):
    billing_details: Optional[str] = None
    account_numbers: List[str] = []
    contact_info: Dict[str, Any] = {}

class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None

class FinancialDetails(BaseModel):
    line_items: List[LineItem] = []
    total_value: Optional[float] = None
    currency: Optional[str] = None
    tax_info: Optional[str] = None
    additional_fees: List[Dict[str, Any]] = []

class PaymentStructure(BaseModel):
    payment_terms: Optional[str] = None  # Net 30, Net 60, etc.
    payment_schedules: List[str] = []
    due_dates: List[str] = []
    payment_methods: List[str] = []
    banking_details: Optional[str] = None

class RevenueClassification(BaseModel):
    recurring_payments: bool = False
    one_time_payments: bool = False
    subscription_model: Optional[str] = None
    billing_cycle: Optional[str] = None
    renewal_terms: Optional[str] = None
    auto_renewal: bool = False

class ServiceLevelAgreement(BaseModel):
    performance_metrics: List[str] = []
    benchmarks: List[str] = []
    penalty_clauses: List[str] = []
    remedies: List[str] = []
    support_terms: Optional[str] = None
    maintenance_terms: Optional[str] = None

class ExtractedData(BaseModel):
    parties: List[PartyInfo] = []
    account_info: Optional[AccountInfo] = None
    financial_details: Optional[FinancialDetails] = None
    payment_structure: Optional[PaymentStructure] = None
    revenue_classification: Optional[RevenueClassification] = None
    sla: Optional[ServiceLevelAgreement] = None
    confidence_scores: Dict[str, float] = {}

class Gap(BaseModel):
    field: str
    description: str
    criticality: str  # high, medium, low

class ContractResponse(BaseModel):
    contract_id: str
    filename: str
    status: str
    extracted_data: Optional[ExtractedData] = None
    score: Optional[float] = None
    gaps: List[Gap] = []
    processed_at: Optional[datetime] = None

class ContractSummary(BaseModel):
    contract_id: str
    filename: str
    status: str
    score: Optional[float] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

class ContractListResponse(BaseModel):
    contracts: List[ContractSummary]
    total: int
    page: int
    limit: int
    pages: int
