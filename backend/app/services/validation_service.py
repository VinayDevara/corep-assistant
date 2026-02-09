from typing import List, Dict
from app.models import TemplateField, ValidationIssue, TemplateType


class ValidationService:
    """Service for validating COREP template data"""
    
    def __init__(self):
        self.validation_rules = {
            "must_be_positive": self._validate_positive,
            "must_be_negative_or_zero": self._validate_negative_or_zero,
            "required_field": self._validate_required
        }
    
    def _validate_positive(self, value) -> bool:
        """Check if value is positive"""
        if value is None:
            return False
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False
    
    def _validate_negative_or_zero(self, value) -> bool:
        """Check if value is negative or zero"""
        if value is None:
            return True  # Adjustments can be zero
        try:
            return float(value) <= 0
        except (ValueError, TypeError):
            return False
    
    def _validate_required(self, value) -> bool:
        """Check if required field has a value"""
        return value is not None
    
    def validate_fields(
        self,
        fields: List[TemplateField],
        template_type: TemplateType,
        template_schema: Dict
    ) -> List[ValidationIssue]:
        """Validate template fields against schema and business rules"""
        
        issues = []
        field_map = {f.field_id: f for f in fields}
        
        # Validate each section
        for section in template_schema.get("sections", []):
            for field_def in section.get("fields", []):
                field_id = field_def["field_id"]
                field = field_map.get(field_id)
                
                # Check required fields
                if field_def.get("required", False):
                    if not field or field.value is None:
                        issues.append(ValidationIssue(
                            severity="error",
                            field_id=field_id,
                            message=f"Required field '{field_def['field_name']}' is missing",
                            rule="required_field"
                        ))
                        continue
                
                # Skip validation if field not populated
                if not field or field.value is None:
                    continue
                
                # Apply validation rules
                for rule_name in field_def.get("validation_rules", []):
                    if rule_name in self.validation_rules:
                        validator = self.validation_rules[rule_name]
                        if not validator(field.value):
                            issues.append(ValidationIssue(
                                severity="error",
                                field_id=field_id,
                                message=f"Field '{field_def['field_name']}' failed validation: {rule_name}",
                                rule=rule_name
                            ))
                
                # Check confidence score
                if field.confidence_score < 0.5:
                    issues.append(ValidationIssue(
                        severity="warning",
                        field_id=field_id,
                        message=f"Low confidence score ({field.confidence_score:.0%}) for field '{field_def['field_name']}'",
                        rule="confidence_threshold"
                    ))
        
        # Apply cross-field validation
        cross_validation_issues = self._validate_cross_field_rules(
            fields, template_type, template_schema
        )
        issues.extend(cross_validation_issues)
        
        return issues
    
    def _validate_cross_field_rules(
        self,
        fields: List[TemplateField],
        template_type: TemplateType,
        template_schema: Dict
    ) -> List[ValidationIssue]:
        """Validate cross-field business rules"""
        
        issues = []
        field_map = {f.field_id: f.value for f in fields if f.value is not None}
        
        if template_type == TemplateType.OWN_FUNDS_CR1:
            issues.extend(self._validate_cr1_rules(field_map))
        elif template_type == TemplateType.CAPITAL_REQUIREMENTS_CR2:
            issues.extend(self._validate_cr2_rules(field_map))
        
        return issues
    
    def _validate_cr1_rules(self, field_map: Dict) -> List[ValidationIssue]:
        """Validate CR1-specific business rules"""
        
        issues = []
        
        # V2: Total CET1 calculation
        cet1_components = [
            field_map.get("CR1_010_010", 0),
            field_map.get("CR1_020_010", 0),
            field_map.get("CR1_030_010", 0),
            field_map.get("CR1_040_010", 0),
            field_map.get("CR1_050_010", 0)
        ]
        adjustments = field_map.get("CR1_100_010", 0)
        calculated_cet1 = sum(cet1_components) + adjustments  # adjustments are negative
        reported_cet1 = field_map.get("CR1_500_010")
        
        if reported_cet1 is not None:
            if abs(calculated_cet1 - reported_cet1) > 1:  # Allow for rounding
                issues.append(ValidationIssue(
                    severity="error",
                    field_id="CR1_500_010",
                    message=f"Total CET1 ({reported_cet1}) does not match sum of components ({calculated_cet1:.2f})",
                    rule="cr1_cet1_calculation"
                ))
        
        # V3: Total Tier 1 calculation
        cet1 = field_map.get("CR1_500_010", 0)
        at1 = field_map.get("CR1_150_010", 0)
        calculated_tier1 = cet1 + at1
        reported_tier1 = field_map.get("CR1_600_010")
        
        if reported_tier1 is not None:
            if abs(calculated_tier1 - reported_tier1) > 1:
                issues.append(ValidationIssue(
                    severity="error",
                    field_id="CR1_600_010",
                    message=f"Total Tier 1 ({reported_tier1}) does not match CET1 + AT1 ({calculated_tier1:.2f})",
                    rule="cr1_tier1_calculation"
                ))
        
        # V4: Total own funds calculation
        tier1 = field_map.get("CR1_600_010", 0)
        tier2 = field_map.get("CR1_200_010", 0)
        calculated_own_funds = tier1 + tier2
        reported_own_funds = field_map.get("CR1_700_010")
        
        if reported_own_funds is not None:
            if abs(calculated_own_funds - reported_own_funds) > 1:
                issues.append(ValidationIssue(
                    severity="error",
                    field_id="CR1_700_010",
                    message=f"Total own funds ({reported_own_funds}) does not match Tier 1 + Tier 2 ({calculated_own_funds:.2f})",
                    rule="cr1_own_funds_calculation"
                ))
        
        # V6: Minimum capital requirements (if RWA available)
        # This would require RWA data from CR2 template
        cet1_amount = field_map.get("CR1_500_010")
        if cet1_amount is not None and cet1_amount < 0:
            issues.append(ValidationIssue(
                severity="error",
                field_id="CR1_500_010",
                message="CET1 capital cannot be negative",
                rule="cr1_minimum_cet1"
            ))
        
        return issues
    
    def _validate_cr2_rules(self, field_map: Dict) -> List[ValidationIssue]:
        """Validate CR2-specific business rules"""
        
        issues = []
        
        # Validate total RWA calculation
        credit_std = field_map.get("CR2_010_010", 0)
        credit_irb = field_map.get("CR2_020_010", 0)
        market = field_map.get("CR2_050_010", 0)
        operational = field_map.get("CR2_060_010", 0)
        
        # RWA = Credit RWA + (Market + Operational own funds requirement * 12.5)
        calculated_rwa = credit_std + credit_irb + (market + operational) * 12.5
        reported_rwa = field_map.get("CR2_100_010")
        
        if reported_rwa is not None:
            if abs(calculated_rwa - reported_rwa) > 1:
                issues.append(ValidationIssue(
                    severity="error",
                    field_id="CR2_100_010",
                    message=f"Total RWA ({reported_rwa}) does not match calculated RWA ({calculated_rwa:.2f})",
                    rule="cr2_rwa_calculation"
                ))
        
        # Check that at least one credit risk approach is used
        if credit_std == 0 and credit_irb == 0:
            issues.append(ValidationIssue(
                severity="warning",
                field_id="CR2_010_010",
                message="No credit risk exposure reported (both Standardised and IRB are zero)",
                rule="cr2_credit_risk_required"
            ))
        
        return issues
    
    def generate_validation_summary(self, issues: List[ValidationIssue]) -> Dict:
        """Generate summary of validation results"""
        
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        info_count = sum(1 for i in issues if i.severity == "info")
        
        return {
            "total_issues": len(issues),
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "is_valid": error_count == 0
        }
