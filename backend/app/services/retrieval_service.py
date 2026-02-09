import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import os


class RetrievalService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB and embedding model"""
        
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="regulatory_documents",
            metadata={"description": "PRA Rulebook and COREP guidance"}
        )
        
        # Initialize with sample data if empty
        if self.collection.count() == 0:
            self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample PRA Rulebook and COREP guidance"""
        
        sample_documents = [
            {
                "id": "pra_crd_art4_1",
                "document": "PRA Rulebook - CRD",
                "section": "Article 4(1) - Own Funds",
                "content": """Own funds shall consist of the sum of Tier 1 capital and Tier 2 capital. 
Tier 1 capital shall consist of Common Equity Tier 1 (CET1) capital and Additional Tier 1 (AT1) capital. 
Common Equity Tier 1 capital shall include: (a) capital instruments, provided the conditions laid out in Article 28 are met; 
(b) share premium accounts related to the instruments referred to in point (a); (c) retained earnings; 
(d) accumulated other comprehensive income; (e) other reserves; (f) funds for general banking risk."""
            },
            {
                "id": "pra_crd_art28",
                "document": "PRA Rulebook - CRD",
                "section": "Article 28 - CET1 Instruments",
                "content": """Capital instruments shall qualify as Common Equity Tier 1 instruments only if all of the following conditions are met:
(a) the instruments are issued directly by the institution with the prior approval of the owners of the institution or, 
where permitted under applicable national law, the management body of the institution;
(b) the instruments are paid up and their purchase is not funded directly or indirectly by the institution;
(c) the instruments meet all the criteria for classification as equity capital under applicable accounting standards;
(d) the instruments are clearly and separately disclosed on the balance sheet in the financial statements;
(e) the instruments are perpetual."""
            },
            {
                "id": "pra_crd_art72",
                "document": "PRA Rulebook - CRD",
                "section": "Article 72 - Tier 2 Capital",
                "content": """Tier 2 items shall comprise the following: (a) capital instruments and subordinated loans that meet the conditions laid down in Article 63; 
(b) the share premium accounts related to the instruments and subordinated loans referred to in point (a); 
(c) the amount of the items referred to in Article 62(1)(c) and (d) that is not included in Tier 1; 
(d) where applicable, any qualifying regulatory adjustments that exceed the Tier 1 capital of the institution."""
            },
            {
                "id": "corep_cr1_instructions_1",
                "document": "COREP CR1 Instructions",
                "section": "Template CR1 - Own Funds",
                "content": """The Own Funds template (CR1) shall be completed by all institutions. This template provides a breakdown of an institution's own funds into its constituent elements.
Row 010: Common Equity Tier 1 (CET1) capital - report the total amount of Common Equity Tier 1 capital instruments and related share premium.
Row 020: Retained earnings - report accumulated retained earnings including interim or year-end profits.
Row 030: Accumulated other comprehensive income (OCI) - report the amount of accumulated OCI recognized in equity.
Row 040: Other reserves - report amounts held in other reserve categories."""
            },
            {
                "id": "corep_cr1_instructions_2",
                "document": "COREP CR1 Instructions",
                "section": "Template CR1 - Regulatory Adjustments",
                "content": """Row 100: Total regulatory adjustments to CET1 - report the sum of all regulatory deductions from CET1 capital.
Row 110: Intangible assets - report the amount of intangible assets (net of associated tax liability) to be deducted from CET1.
Row 120: Deferred tax assets - report deferred tax assets that rely on future profitability and do not arise from temporary differences.
Row 150: Additional Tier 1 (AT1) capital before regulatory adjustments - report qualifying AT1 instruments and related share premium.
Row 200: Tier 2 capital before regulatory adjustments - report qualifying Tier 2 instruments and subordinated loans."""
            },
            {
                "id": "pra_capital_requirements_1",
                "document": "PRA Rulebook - Capital Requirements",
                "section": "Article 92 - Own Funds Requirements",
                "content": """Institutions shall at all times satisfy the following own funds requirements:
(a) a Common Equity Tier 1 capital ratio of 4.5%;
(b) a Tier 1 capital ratio of 6%;
(c) a total capital ratio of 8%.
The Common Equity Tier 1 capital ratio shall be calculated as the Common Equity Tier 1 capital of the institution divided by the total risk exposure amount, expressed as a percentage.
The Tier 1 capital ratio shall be calculated as the Tier 1 capital of the institution divided by the total risk exposure amount, expressed as a percentage.
The total capital ratio shall be calculated as the own funds of the institution divided by the total risk exposure amount, expressed as a percentage."""
            },
            {
                "id": "corep_cr2_instructions_1",
                "document": "COREP CR2 Instructions",
                "section": "Template CR2 - Capital Requirements",
                "content": """The Capital Requirements template (CR2) shall be completed by all institutions to report their capital requirements for credit risk, market risk, and operational risk.
Row 010: Credit risk (standardised approach) - report the total risk exposure amount for credit risk calculated using the standardised approach.
Row 020: Credit risk (IRB approach) - report the total risk exposure amount for credit risk calculated using internal ratings-based approaches.
Row 050: Market risk - report the total own funds requirements for market risk positions.
Row 060: Operational risk - report the total own funds requirements for operational risk.
Row 100: Total risk exposure amount - sum of all risk exposure amounts across credit, market, and operational risk."""
            },
            {
                "id": "pra_crd_art36",
                "document": "PRA Rulebook - CRD",
                "section": "Article 36 - Regulatory Adjustments",
                "content": """Institutions shall make the following deductions from Common Equity Tier 1 items:
(a) losses for the current financial year;
(b) intangible assets, net of any associated deferred tax liability;
(c) a deferred tax asset that relies on future profitability and does not arise from temporary differences net of any associated deferred tax liability, where the conditions in point (a) of Article 38(3) are met;
(d) negative amounts resulting from the calculation of expected loss amounts;
(e) any increase in equity that results from securitised assets;
(f) gains or losses on liabilities valued at fair value resulting from changes in the institution's own credit standing."""
            },
            {
                "id": "pra_consolidation_1",
                "document": "PRA Rulebook - Consolidation",
                "section": "Part 1 - Scope of Consolidation",
                "content": """For the purposes of prudential consolidation, institutions shall include in the consolidated situation all subsidiaries that are institutions or financial institutions. 
The consolidation shall include the full consolidation of any subsidiary that is an institution or financial institution. 
Participations in subsidiaries shall be included at the proportional share of own funds and own funds requirements where permitted.
Institutions shall apply the requirements of this Part on a consolidated basis to the extent and in the manner prescribed by the PRA."""
            },
            {
                "id": "corep_validation_1",
                "document": "COREP Validation Rules",
                "section": "CR1 Cross-checks",
                "content": """The following validation rules shall be applied to the CR1 template:
V1: Row 010 (CET1 capital instruments) must be greater than zero.
V2: Row 500 (Total CET1 capital) = Sum of rows 010 to 040 minus row 100 (regulatory adjustments).
V3: Row 600 (Total Tier 1 capital) = Row 500 (CET1) plus row 150 (AT1 capital after adjustments).
V4: Row 700 (Total own funds) = Row 600 (Tier 1) plus row 200 (Tier 2 capital after adjustments).
V5: All capital amounts must be reported in thousands of the reporting currency.
V6: CET1 ratio must be at least 4.5%, Tier 1 ratio at least 6%, Total capital ratio at least 8%."""
            }
        ]
        
        # Add documents to collection
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["content"] for doc in sample_documents]
        metadatas = [
            {
                "document": doc["document"],
                "section": doc["section"]
            }
            for doc in sample_documents
        ]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Initialized {len(sample_documents)} regulatory documents")
    
    def retrieve_relevant_documents(
        self,
        query: str,
        template_type: str,
        n_results: int = 5
    ) -> List[Dict]:
        """Retrieve relevant regulatory documents for a query"""
        
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        relevant_docs = []
        if results and results['documents']:
            for i, doc_content in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if 'distances' in results else 0.0
                
                # Calculate relevance score (1 - normalized distance)
                relevance_score = max(0.0, 1.0 - distance)
                
                relevant_docs.append({
                    "document": metadata.get("document", "Unknown"),
                    "section": metadata.get("section", "Unknown"),
                    "paragraph": metadata.get("paragraph", "N/A"),
                    "content": doc_content,
                    "relevance_score": relevance_score
                })
        
        return relevant_docs
    
    def add_document(self, doc_id: str, content: str, metadata: Dict):
        """Add a new regulatory document to the collection"""
        
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata]
        )
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the document collection"""
        
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name
        }
