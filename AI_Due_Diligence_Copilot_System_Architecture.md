# AI Due Diligence Copilot - System Architecture

## Project Overview

AI Due Diligence Copilot is an enterprise AI platform for analyzing
financial documents, company filings, investor presentations, and market
reports using RAG and AI agents.

## High Level Architecture

    User
     |
    Next.js Frontend
     |
    FastAPI Backend
     |
    +----------------+
    | Auth Service   |
    | Document Svc   |
    | AI Service     |
    +----------------+
     |
    +----------------+
    | PostgreSQL     |
    | AWS S3         |
    | Redis Queue    |
    | Vector DB      |
    +----------------+

## Document Processing Pipeline

    PDF Upload
     |
    File Validation
     |
    S3 Storage
     |
    Celery Worker
     |
    Text Extraction
     |
    Chunking
     |
    Embedding Generation
     |
    Vector Database

## RAG Flow

    User Question
     |
    Create Embedding
     |
    Vector Search
     |
    Retrieve Relevant Documents
     |
    LLM Processing
     |
    Answer + Citations

## AI Agent Architecture

    AI Orchestrator

        |
    -------------------------
    |          |            |
    Financial  Risk       Market
    Agent      Agent      Agent

        |
    Investment Thesis Agent

        |
    Report Generator

## Database Entities

### Organization

-   id
-   name
-   industry

### User

-   id
-   name
-   email
-   role
-   organization_id

### Company

-   id
-   name
-   ticker
-   industry

### Document

-   id
-   company_id
-   file_name
-   file_url
-   status

### Document Chunk

-   id
-   document_id
-   content
-   page_number

### Analysis

-   id
-   company_id
-   analysis_type
-   result JSON

### Reports

-   id
-   company_id
-   file_url

### Chat Messages

-   user questions
-   AI answers
-   sources

## Technology Stack

Backend: - FastAPI - Python - SQLAlchemy

Database: - PostgreSQL - pgvector

AI: - LangGraph - LLM - Embeddings

Storage: - AWS S3

Queue: - Redis - Celery

Frontend: - Next.js

## Complete Flow

User uploads company report

↓

Document processing

↓

Embedding creation

↓

Vector storage

↓

AI retrieval

↓

Agent analysis

↓

Investment report generation
