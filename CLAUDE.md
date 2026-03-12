# FP&A Dream

## Overview
FP&A (Financial Planning & Analysis) software for small businesses, inspired by Anaplan.
Replicates core Anaplan features scaled for SMBs, with the added ability to connect to and pull data from external websites/services.

## Target Users
Small businesses that need enterprise-grade FP&A capabilities without Anaplan's cost/complexity.

## Core Features (Planned)
- Multi-dimensional financial modeling (like Anaplan's hyperblock engine)
- Budgeting & forecasting
- Scenario planning
- Dashboards & reporting
- Data integration with external websites/APIs
- Collaboration tools

## Tech Stack
- **Frontend**: React + TypeScript (complex data grids, dashboards)
- **Backend**: Python + FastAPI (financial calculations, Pandas/NumPy for modeling)
- **Database**: PostgreSQL (relational financial data, multi-tenant)
- **Auth**: OAuth2 (Xero, MYOB integrations)

## External Integrations
- **Xero** — accounting data (P&L, balance sheet, cash flow) via Xero API + Python SDK
- **MYOB** — accounting data via MYOB AccountRight / Essentials API
- **Point of Sale** — Square, Vend/Lightspeed (future phase)

## Build Order
1. **Phase 1 — Data Imports**
   - OAuth2 connection flows for Xero and MYOB
   - Data sync: chart of accounts, transactions, reports
   - Normalized data model in PostgreSQL
2. **Phase 2 — Modeling Engine**
   - Multi-dimensional calculation engine (inspired by Anaplan hyperblock)
   - Budgeting, forecasting, scenario planning
3. **Phase 3 — Dashboards & Reporting**
4. **Phase 4 — POS Integrations**

## Development
<!-- Setup instructions TBD -->

## Notes
- Competitor reference: Anaplan (enterprise), targeting SMB segment
- Key differentiator: affordable, pre-built integrations with SMB-popular tools (Xero, MYOB, POS)
