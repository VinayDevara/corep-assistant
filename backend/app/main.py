from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from datetime import datetime
from typing import Dict
import os
from pathlib import Path
from dotenv import load_dotenv

from app.models import (
    QueryRequest, QueryResponse, RegulatoryReference,
    TemplateField, TemplateOutput, AuditLogEntry
)
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.services.template_service import TemplateService
from app.services.validation_service import ValidationService


# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Global service instances
services = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    print("Initializing services...")
    
    services["llm"] = LLMService()
    services["retrieval"] = RetrievalService()
    services["template"] = TemplateService()
    services["validation"] = ValidationService()
    
    print("Services initialized successfully")
    print(f"Document collection stats: {services['retrieval'].get_collection_stats()}")
    
    yield
    
    # Cleanup on shutdown
    print("Shutting down services...")


app = FastAPI(
    title="PRA COREP Reporting Assistant",
    description="LLM-assisted regulatory reporting tool for UK banks",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PRA COREP Reporting Assistant",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "llm": "ready" if "llm" in services else "not initialized",
            "retrieval": "ready" if "retrieval" in services else "not initialized",
            "template": "ready" if "template" in services else "not initialized",
            "validation": "ready" if "validation" in services else "not initialized"
        },
        "document_count": services["retrieval"].get_collection_stats()["total_documents"] if "retrieval" in services else 0
    }


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a regulatory reporting query
    
    This endpoint:
    1. Retrieves relevant regulatory documents
    2. Generates structured output using LLM
    3. Validates the output
    4. Creates an audit log
    """
    
    start_time = time.time()
    
    try:
        # Step 1: Retrieve relevant regulatory documents
        print(f"Processing query: {request.question[:100]}...")
        
        retrieval_service = services["retrieval"]
        relevant_docs = retrieval_service.retrieve_relevant_documents(
            query=request.question,
            template_type=request.template_type.value,
            n_results=5
        )
        
        print(f"Retrieved {len(relevant_docs)} relevant documents")
        
        # Step 2: Generate structured output using LLM
        llm_service = services["llm"]
        llm_output = llm_service.generate_structured_output(
            query=request.question,
            scenario=request.scenario,
            regulatory_context=[
                {
                    "document": doc["document"],
                    "section": doc["section"],
                    "content": doc["content"]
                }
                for doc in relevant_docs
            ],
            template_type=request.template_type.value
        )
        
        print(f"Generated structured output with {len(llm_output.get('fields', []))} fields")
        
        # Step 3: Map LLM output to template fields
        template_service = services["template"]
        template_fields = []
        audit_log = []
        
        for field_data in llm_output.get("fields", []):
            template_field = TemplateField(
                field_id=field_data["field_id"],
                field_name=field_data["field_name"],
                value=field_data.get("value"),
                justification=field_data.get("justification", ""),
                regulatory_references=field_data.get("regulatory_references", []),
                confidence_score=field_data.get("confidence_score", 0.5)
            )
            template_fields.append(template_field)
            
            # Create audit log entries
            for ref in field_data.get("regulatory_references", []):
                audit_log.append(AuditLogEntry(
                    timestamp=datetime.utcnow(),
                    field_id=field_data["field_id"],
                    regulatory_reference=ref,
                    justification=field_data.get("justification", "")
                ))
        
        # Step 4: Validate the output
        validation_service = services["validation"]
        template_schema = template_service.get_template_schema(request.template_type)
        
        validation_issues = validation_service.validate_fields(
            fields=template_fields,
            template_type=request.template_type,
            template_schema=template_schema
        )
        
        print(f"Validation completed with {len(validation_issues)} issues")
        
        # Step 5: Build response
        processing_time = time.time() - start_time
        
        response = QueryResponse(
            query=request.question,
            scenario=request.scenario,
            regulatory_references=[
                RegulatoryReference(**doc) for doc in relevant_docs
            ],
            template_output=TemplateOutput(
                template_type=request.template_type,
                fields=template_fields,
                validation_issues=validation_issues,
                audit_log=audit_log,
                metadata={
                    "summary": llm_output.get("summary", ""),
                    "key_considerations": llm_output.get("key_considerations", []),
                    "validation_summary": validation_service.generate_validation_summary(validation_issues)
                }
            ),
            processing_time_seconds=processing_time,
            llm_model="llama-3.1-70b-versatile"
        )
        
        return response
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/api/templates/{template_type}")
async def get_template_schema(template_type: str):
    """Get the schema for a specific COREP template"""
    
    try:
        from app.models import TemplateType
        template_enum = TemplateType(template_type)
        
        template_service = services["template"]
        schema = template_service.get_template_schema(template_enum)
        
        return schema
        
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Template type '{template_type}' not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving template schema: {str(e)}"
        )


@app.get("/api/documents/stats")
async def get_document_stats():
    """Get statistics about the regulatory document collection"""
    
    retrieval_service = services["retrieval"]
    return retrieval_service.get_collection_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
