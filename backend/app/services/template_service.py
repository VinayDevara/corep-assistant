from typing import Dict, List
from app.models import TemplateType, TemplateField


class TemplateService:
    """Service for managing COREP template schemas and rendering"""
    
    def __init__(self):
        self.templates = {
            TemplateType.OWN_FUNDS_CR1: self._get_cr1_schema(),
            TemplateType.CAPITAL_REQUIREMENTS_CR2: self._get_cr2_schema()
        }
    
    def _get_cr1_schema(self) -> Dict:
        """Define the CR1 (Own Funds) template schema"""
        return {
            "template_name": "CR1 - Own Funds",
            "description": "Breakdown of institution's own funds and regulatory capital",
            "sections": [
                {
                    "section_id": "cet1_capital",
                    "section_name": "Common Equity Tier 1 Capital",
                    "fields": [
                        {
                            "field_id": "CR1_010_010",
                            "field_name": "Capital instruments and related share premium accounts",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"]
                        },
                        {
                            "field_id": "CR1_020_010",
                            "field_name": "Retained earnings",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        },
                        {
                            "field_id": "CR1_030_010",
                            "field_name": "Accumulated other comprehensive income",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        },
                        {
                            "field_id": "CR1_040_010",
                            "field_name": "Other reserves",
                            "data_type": "number",
                            "required": False,
                            "validation_rules": []
                        },
                        {
                            "field_id": "CR1_050_010",
                            "field_name": "Funds for general banking risk",
                            "data_type": "number",
                            "required": False,
                            "validation_rules": []
                        }
                    ]
                },
                {
                    "section_id": "cet1_adjustments",
                    "section_name": "CET1 Regulatory Adjustments",
                    "fields": [
                        {
                            "field_id": "CR1_100_010",
                            "field_name": "Total regulatory adjustments to CET1",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_negative_or_zero"]
                        },
                        {
                            "field_id": "CR1_110_010",
                            "field_name": "Intangible assets (net of tax)",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        },
                        {
                            "field_id": "CR1_120_010",
                            "field_name": "Deferred tax assets",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        }
                    ]
                },
                {
                    "section_id": "tier1_tier2",
                    "section_name": "Additional Tier 1 and Tier 2 Capital",
                    "fields": [
                        {
                            "field_id": "CR1_150_010",
                            "field_name": "Additional Tier 1 capital",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        },
                        {
                            "field_id": "CR1_200_010",
                            "field_name": "Tier 2 capital",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        }
                    ]
                },
                {
                    "section_id": "totals",
                    "section_name": "Total Own Funds",
                    "fields": [
                        {
                            "field_id": "CR1_500_010",
                            "field_name": "Total Common Equity Tier 1 capital",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"],
                            "formula": "sum(CR1_010_010:CR1_050_010) - CR1_100_010"
                        },
                        {
                            "field_id": "CR1_600_010",
                            "field_name": "Total Tier 1 capital",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"],
                            "formula": "CR1_500_010 + CR1_150_010"
                        },
                        {
                            "field_id": "CR1_700_010",
                            "field_name": "Total own funds",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"],
                            "formula": "CR1_600_010 + CR1_200_010"
                        }
                    ]
                }
            ]
        }
    
    def _get_cr2_schema(self) -> Dict:
        """Define the CR2 (Capital Requirements) template schema"""
        return {
            "template_name": "CR2 - Capital Requirements",
            "description": "Institution's capital requirements by risk type",
            "sections": [
                {
                    "section_id": "credit_risk",
                    "section_name": "Credit Risk",
                    "fields": [
                        {
                            "field_id": "CR2_010_010",
                            "field_name": "Credit risk (Standardised approach) - RWA",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"]
                        },
                        {
                            "field_id": "CR2_020_010",
                            "field_name": "Credit risk (IRB approach) - RWA",
                            "data_type": "number",
                            "required": False,
                            "validation_rules": ["must_be_positive"]
                        }
                    ]
                },
                {
                    "section_id": "other_risks",
                    "section_name": "Other Risk Types",
                    "fields": [
                        {
                            "field_id": "CR2_050_010",
                            "field_name": "Market risk - Own funds requirement",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": []
                        },
                        {
                            "field_id": "CR2_060_010",
                            "field_name": "Operational risk - Own funds requirement",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"]
                        }
                    ]
                },
                {
                    "section_id": "total_requirements",
                    "section_name": "Total Capital Requirements",
                    "fields": [
                        {
                            "field_id": "CR2_100_010",
                            "field_name": "Total risk exposure amount",
                            "data_type": "number",
                            "required": True,
                            "validation_rules": ["must_be_positive"],
                            "formula": "sum(CR2_010_010, CR2_020_010) + (CR2_050_010 + CR2_060_010) * 12.5"
                        }
                    ]
                }
            ]
        }
    
    def get_template_schema(self, template_type: TemplateType) -> Dict:
        """Get the schema for a specific template type"""
        return self.templates.get(template_type, {})
    
    def get_all_field_ids(self, template_type: TemplateType) -> List[str]:
        """Get all field IDs for a template"""
        schema = self.get_template_schema(template_type)
        field_ids = []
        
        for section in schema.get("sections", []):
            for field in section.get("fields", []):
                field_ids.append(field["field_id"])
        
        return field_ids
    
    def render_template_html(
        self,
        template_type: TemplateType,
        fields: List[TemplateField]
    ) -> str:
        """Render populated template as HTML"""
        
        schema = self.get_template_schema(template_type)
        field_map = {f.field_id: f for f in fields}
        
        html = f"""
        <div class="corep-template">
            <h2>{schema.get('template_name', 'COREP Template')}</h2>
            <p class="description">{schema.get('description', '')}</p>
        """
        
        for section in schema.get("sections", []):
            html += f"""
            <div class="template-section">
                <h3>{section['section_name']}</h3>
                <table class="template-table">
                    <thead>
                        <tr>
                            <th>Field ID</th>
                            <th>Field Name</th>
                            <th>Value</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for field_def in section.get("fields", []):
                field_id = field_def["field_id"]
                field = field_map.get(field_id)
                
                value_display = field.value if field else "N/A"
                confidence_display = f"{field.confidence_score:.0%}" if field else "N/A"
                
                html += f"""
                <tr>
                    <td class="field-id">{field_id}</td>
                    <td class="field-name">{field_def['field_name']}</td>
                    <td class="field-value">{value_display}</td>
                    <td class="confidence">{confidence_display}</td>
                </tr>
                """
            
            html += """
                    </tbody>
                </table>
            </div>
            """
        
        html += "</div>"
        
        return html
