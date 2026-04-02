# Design and Implementation of a Hybrid

# Retrieval-Based Conversational Assistant for University Admission Policies

## Supervisor: Miss Humaira Tariq


## Abstract

University admission policies are often presented in lengthy and technical documents that are
difficult for prospective students to understand. As a result, many applicants rely on informal
sources and word-of-mouth information, which may lead to misinformation and incorrect
applications. This project proposes the design and implementation of a Retrieval-Augmented
Generation (RAG) based conversational assistant for interpreting university admission policies.
The proposed system integrates hybrid information retrieval techniques with large language
models to provide accurate, citation-grounded responses in simple English and Roman Urdu. The
system processes official admission documents, constructs a structured knowledge base, and
retrieves relevant information in response to user queries. An evaluation framework will be
developed to assess retrieval accuracy, answer correctness, and citation reliability. The project
aims to improve accessibility to authentic admission information while demonstrating the
practical application of modern natural language processing and information retrieval techniques.

### 1. Introduction

University admission procedures involve complex policies, eligibility rules, deadlines, and
documentation requirements, which are often difficult for students to understand. As a result,
many applicants rely on informal sources or repeated visits to admission offices.
At the University of Karachi, limited access to clear and reliable admission information can lead
to misunderstandings, incorrect applications, and missed deadlines.
Recent advances in artificial intelligence, especially Retrieval-Augmented Generation (RAG)
systems, offer an effective solution by combining document retrieval with language models to
provide accurate, verified, and user-friendly responses. This project aims to develop an
intelligent admission assistance system to improve access to admission-related information.

## 2. Literature Review

#### 2.1 Chatbots in Educational Support Systems

Previous research has demonstrated the effectiveness of chatbots in supporting students in
academic advising, administrative services, and learning assistance. Educational chatbots have
been used to answer frequently asked questions, guide students through procedures, and reduce
administrative workload.

#### 2.2 Retrieval-Augmented Generation (RAG)

Retrieval-Augmented Generation integrates document retrieval with language model generation.
Instead of generating responses solely from model knowledge, RAG systems retrieve relevant
documents and use them as context for answer generation. This approach improves factual
accuracy and reduces hallucination.


#### 2.3 Hybrid Information Retrieval

Hybrid retrieval combines keyword-based methods such as BM25 with dense vector-based
semantic search. Studies indicate that hybrid approaches outperform single-method retrieval in
domains involving technical and policy-based documents.

#### 2.4 Multilingual and Roman Urdu NLP

Roman Urdu is widely used in informal communication in Pakistan. However, it lacks
standardized spelling and linguistic resources. Prior work highlights challenges in processing
Roman Urdu, including spelling variation and code-mixing with English.

#### 2.5 Research Gap

Existing admission assistance systems rarely support informal or Roman Urdu queries while
providing citation-grounded responses. Furthermore, limited work has been conducted on
applying RAG systems to institutional policy interpretation in multilingual contexts.

## 3. Problem Statement

Prospective students at the University of Karachi face difficulties in understanding admission
policies due to complex documentation, dispersed information sources, and lack of interactive
guidance. Currently, no intelligent system exists that can interpret official admission documents
and provide instant, reliable, and easily understandable responses to informal student queries.

## 4. Objectives

#### 4.1 Primary Objective

To design and implement a hybrid retrieval-based conversational assistant that provides accurate,
citation-grounded responses to admission-related queries.

#### 4.2 Secondary Objectives

```
● To construct a structured knowledge base from official admission documents.
● To develop a query normalization module for informal English and Roman Urdu.
● To implement hybrid retrieval using keyword and semantic search.
● To integrate a RAG-based answer generation system.
● To evaluate system performance using real student queries.
● To develop a user-friendly web interface.
```
## 5. Research Questions

1. Does hybrid retrieval improve retrieval accuracy compared to vector-only search?
2. Does query normalization enhance performance for Roman Urdu queries?


3. Can citation grounding reduce hallucinated responses?
4. How effective is the system in improving access to admission information?

## 6. System Architecture

The proposed system follows a layered architecture designed to efficiently process user queries
and generate reliable responses based on official admission documents.

#### Client Layer:

The client interface is implemented using a **Next.js web application** that provides an interactive
chatbot interface.

#### API Layer:

The backend is developed using **FastAPI** , which manages communication between the frontend,
retrieval engine, and database. It handles query processing, request routing, and response
formatting.

#### Data Layer:

Admission documents are stored in a **Neon PostgreSQL database**.

#### Retrieval Layer:

A hybrid retrieval approach is implemented combining:
● keyword-based full-text search
● semantic vector similarity search
The results from both methods are merged using **Reciprocal Rank Fusion (RRF)** to improve
retrieval accuracy.

#### Generation Layer:

The retrieved document passages are provided as context to a **Large Language Model (LLM)**
which generates responses grounded in the retrieved content, ensuring factual accuracy and
citation-based responses.

#### Administration Layer:

An ingestion module processes new admission documents through parsing, text cleaning,
chunking, and embedding generation before indexing them in the database.


## 7. Integration with Outcome-Based Education (OBE) Systems

Outcome-Based Education (OBE) is a framework used in higher education institutions to
evaluate academic programs based on measurable performance indicators such as enrollment
rates, retention rates, graduation rates, and student success outcomes.
Universities often monitor these indicators through institutional analytics systems and
performance dashboards.
The proposed admission chatbot system can be integrated into the institutional OBE framework
as an **Admission Information Support Module**. By providing accurate and accessible
admission guidance to prospective students, the system helps applicants better understand
admission requirements and procedures.
The proposed system contributes to several institutional performance indicators:

**OBE Indicator** (^) **Contribution of Proposed System**
Enrollment Rate Improves clarity of admission requirements


Admission Accuracy Reduces incorrect applications
Student Retention Helps students choose appropriate programs
Student Satisfaction Provides instant access to admission information
Administrative Efficiency Reduces repetitive inquiries to admission offices
Within the OBE lifecycle, the system operates in the **pre-enrollment phase** , where prospective
students seek admission information before applying.
By improving information accessibility and reducing misinformation, the proposed system
indirectly contributes to improved institutional performance indicators.

## 8. Scope of the Project

#### Included

The system will support the following functionalities:
● Processing official undergraduate admission prospectus documents
● Answering admission-related queries such as eligibility criteria, required documents, and
deadlines
● Supporting queries in **English and Roman Urdu**
● Providing citation-based responses linked to official documents
● Delivering responses through a web-based chatbot interface

#### Excluded

The system will not:
● Predict admission chances or merit rankings
● Process admission applications
● Store personal applicant data
● Replace official admission authorities or decision-making systems

## 9. Methodology


The proposed system will be developed through the following stages:

#### Data Collection:

Official admission prospectus documents and relevant university policies will be collected and
verified.

#### Document Processing:

Documents will be processed using **PyMuPDF** to extract text, remove noise, and divide content
into structured sections.

#### Indexing:

Document sections will be converted into vector embeddings using multilingual embedding
models. These embeddings and metadata will be stored in PostgreSQL using **pgvector** and
full-text indexing.

#### Query Processing:

User queries will be processed through language detection, spelling normalization, and Roman
Urdu standardization.

#### Retrieval:

A hybrid retrieval mechanism combining keyword search and semantic vector search will be
used. Results will be merged using **Reciprocal Rank Fusion (RRF)**.

#### Answer Generation:

Relevant document passages will be provided to a language model to generate responses
grounded in retrieved content.

#### Interface Development:

A responsive web interface will be implemented using **Next.js** to provide an interactive chatbot
experience.

## 10. Evaluation Framework

The system will be evaluated using a structured experimental framework.

#### Dataset:

A dataset of approximately **200 admission-related queries** will be collected, including English,
Roman Urdu, and mixed-language queries.

#### Evaluation Metrics:

```
● Retrieval Accuracy: Recall@5 and Precision@
● Answer Quality: Correct / Partially Correct / Incorrect (human evaluation)
● Citation Accuracy: Correct referencing of source documents
● Response Time: Average system latency
```

#### Comparative Evaluation:

System performance will be compared under different configurations, including hybrid retrieval
versus vector-only retrieval and with or without query normalization.

#### Error Analysis:

Incorrect responses will be analyzed to identify limitations and potential improvements in
retrieval and generation components.

## 11. Ethical and Legal Considerations

```
● Only publicly available documents will be used.
● No personal data will be collected or stored.
● The system will include disclaimers.
● Bias and misinformation risks will be minimized through citation grounding.
● Access will be rate-limited to prevent misuse.
```
## 12. Risk Analysis and Mitigation

```
Risk Impact Mitigation
API downtime System failure Fallback provider
Low accuracy Poor usability Reranking and tuning
Document changes Outdated data Re-indexing pipeline
High cost Budget issues Caching and limits
```
## 13. Feasibility and Cost Analysis

The system primarily uses open-source tools and free-tier services. Expected to remain under
free-tier or low-cost academic usage.. Hardware requirements are minimal, as processing is
CPU-based.

## 14. Project Deliverables

1. Web-based admission chatbot system.
2. Structured admission knowledge base.
3. Performance evaluation report.
4. Source code repository.
5. Deployment package.
6. Final thesis document.
7. Presentation and live demonstration.


## 15. Project Timeline

```
Phase Duration Activities
Planning Weeks 1–2 Literature review, requirements
Data Processing Weeks 3–4 Parsing, cleaning
Indexing Weeks 5–6 Embeddings, storage
Retrieval Weeks 7–8 Hybrid engine
RAG Weeks 9–10 LLM integration
Frontend Weeks 11–12 UI development
Deployment Weeks 13–14 Hosting
Evaluation Weeks 15–16 Testing
Documentation Final Report and slides
```
## 16. Limitations

```
● Depends on document quality.
● Limited to selected admission domains.
● Requires internet access for LLM API.
● Does not replace official authorities.
```
## 17. Future Work

```
● Support for Urdu script.
● Mobile application.
● Voice-based interface.
● Integration with official portals.
● Expansion to postgraduate admissions.
```
## 18. Conclusion

This project proposes a robust and scalable admission assistance system using hybrid retrieval
and RAG techniques. By grounding responses in official documents and supporting informal
language, the system enhances the accessibility and reliability of admission information.The
project demonstrates the practical application of retrieval-augmented language models in higher
education administrative support systems.


