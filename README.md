# AI Welding Inspection Backend

An industrial-grade, AI-powered backend system designed for automated welding quality assurance. This platform leverages computer vision via **Google Gemini AI** to detect structural defects, manages end-to-end inspection lifecycles, processes real-time sensor instrumentation from mobile devices, and automatically generates compliance-ready regulatory reports.

Built using a modern asynchronous stack with **FastAPI**, **PostgreSQL**, and **SQLAlchemy Async ORM**, this system is tailored for high-concurrency, low-latency processing in heavy manufacturing, infrastructure tracking, and automated quality control environments.

---

## 🚀 Key Capabilities & Workflows

* **Asynchronous Execution Pipeline:** Heavily utilizes Python's `async/await` pattern across all data-ingestion layers, database operations, AWS cloud uploads, and remote AI inference calls.
* **Intelligent Defect Classification:** Integrated with Google Gemini AI models to analyze high-resolution weld imagery and map defects like cracks or porosity using bounding boxes.
* **Multi-Sensor Instrumentation Analytics:** Captures weld length, width, and physical telemetry data (accelerometer/gyroscope) directly from the mobile client.
* **Automated Enterprise Reporting:** Dynamic generation of high-fidelity PDF (via ReportLab) and Excel (via OpenPyXL) reports with severity color-coding[cite: 1].
* **Enterprise Security:** Complete OAuth2 JWT authentication with token blacklisting and immutable system-wide Audit Logging[cite: 1].

---

## 🏗️ Technical Architecture

The platform follows a strict decoupled Layered Architecture:

1. **FastAPI Route Layer:** Validates payloads via Pydantic Schemas[cite: 1].
2. **Services Layer:** Modular business logic (Auth, AI, Inspection, Reports)[cite: 1].
3. **Data Access Layer:** SQLAlchemy Async ORM mapping relational entities[cite: 1].
4. **Storage:** AWS S3 for binary chunk storage and high-res image uploads[cite: 1].

---

## 📂 Repository Directory Layout

```text
app/
 ├── api/ v1/ endpoints/       # REST route definitions
 ├── core/                     # Config & JWT security policies
 ├── db/                       # Database engine & async session factories
 ├── models/                   # SQLAlchemy declaration models
 ├── schemas/                  # Pydantic validation structures
 ├── services/                 # Enterprise workflows (The system "Brain")
 ├── utils/                    # S3, ReportLab, Audit Log, IDs
 └── main.py                   # Central bootstrap engine
