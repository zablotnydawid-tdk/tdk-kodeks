# EXIM Knowledge Operating System

## Purpose

The Complex Knowledge Processing Layer now acts as a local Knowledge Operating System. It prevents complex document content from becoming a recommendation without source trace, domain classification, validation level, risk mapping, decision mapping, and human validation where required.

It is built for mixed operator material:

- field procedures,
- EMS/HEMS algorithms,
- OZE subsidy material,
- regulatory audit,
- VPP / CSIRE / net-billing,
- 253V diagnostics,
- heat pumps,
- BESS,
- client reports and evidence.

## Flow

```text
DOCUMENT
-> INGESTION
-> CLASSIFICATION
-> SOURCE GRAPH
-> EVIDENCE MAP
-> RISK MAP
-> DECISION MAP
-> REPORT ENGINE
-> HUMAN VALIDATION
```

## Modules

| Module | Role |
| --- | --- |
| `knowledge/ingestion_engine.py` | Knowledge OS orchestration entry point |
| `knowledge/ocr_pipeline.py` | Stage 2 OCR/PDF adapter alias |
| `knowledge/semantic_chunker.py` | Stage 2 chunking adapter |
| `knowledge/source_graph_builder.py` | Stage 2 source graph adapter |
| `knowledge/document_ingestor.py` | Entry point for local document ingestion |
| `knowledge/pdf_ocr_pipeline.py` | Local PDF text extraction adapter; OCR gaps become human review |
| `knowledge/chunker.py` | Claim/chunk creation with trace object |
| `knowledge/domain_classifier.py` | Domain classification for complex knowledge |
| `knowledge/source_graph.py` | Source graph, dependency map, risk map |
| `knowledge/evidence_mapper.py` | Evidence type and confidence mapping |
| `knowledge/risk_mapper.py` | Knowledge risk score, SAFE state and metric trace |
| `knowledge/decision_mapper.py` | Output gate and decision map |
| `knowledge/report_context_builder.py` | Validated report context builder |
| `knowledge/regulatory_validator.py` | Human validation gates for regulatory/subsidy/billing/VPP/253V claims |
| `knowledge/report_generator.py` | Operator-facing markdown report |
| `knowledge/human_review_queue.py` | Human review queue for blocked claims |

## Knowledge Domains

```text
REGULATORY
TECHNICAL
FIELD_PROCEDURE
FINANCIAL
SUBSIDY
BILLING
VPP_ALGORITHM
CLIENT_EVIDENCE
```

## Trace Contract

Every chunk carries:

```json
{
  "source_file": "",
  "page": 0,
  "domain": "",
  "claim": "",
  "evidence_type": "",
  "confidence": 0.0,
  "requires_human_review": true
}
```

## Safety Rule

```text
No recommendation without trace.
No trace without source.
No source without classification.
No output without validation level.
```

Complex document content cannot become recommendation without:

- source trace,
- domain classification,
- source graph placement,
- evidence mapping,
- risk map,
- decision map,
- validation status,
- human validation when required.

Regulatory, subsidy, billing, VPP algorithm and 253V diagnostic content are blocked from client recommendation until reviewed.
