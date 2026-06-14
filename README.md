# SOP Creator

An AI-powered web application that converts unstructured documents into clean, structured Standard Operating Procedures (SOPs).

Upload a PDF, DOCX, XLSX, image, or plain text file — the app extracts the content, sends it to Azure AI, and returns a formatted SOP you can edit in the browser and download as a PDF.

---

## Features

- **Multi-format ingestion** — PDF, DOCX, XLSX, PNG, JPG, TXT
- **AI extraction** — Azure AI (GPT-4.1-mini) reads the document and identifies major steps and how to perform them
- **Inline editing** — click any field in the generated SOP to edit it directly
- **Download as PDF** — exports the edited SOP as a formatted A4 PDF
- **Copy as Text** — copies the full SOP to clipboard as plain text
- **No page reloads** — HTMX handles form submission and result injection without JavaScript frameworks

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | HTMX + Jinja2 templates |
| AI | Azure AI Projects SDK → GPT-4.1-mini |
| PDF extraction | PyMuPDF |
| DOCX extraction | python-docx + lxml (ordered text + images) |
| XLSX extraction | openpyxl |
| PDF export | html2pdf.js (client-side) |

---

## Project Structure

```
sop_creator/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── .env.example                     # Environment variable template
├── app/
│   ├── config.py                    # Loads environment variables
│   ├── templates/
│   │   ├── base.html                # Shared layout + HTMX + html2pdf CDN
│   │   ├── index.html               # Upload form
│   │   └── partials/
│   │       └── sop_result.html      # Result fragment injected by HTMX
│   ├── static/
│   │   └── style.css
│   └── modules/
│       ├── extractor/
│       │   └── extractor.py         # File → ordered content blocks
│       ├── ai/
│       │   └── client.py            # Azure AI call + SOP parser
│       └── documents/
│           └── router.py            # GET / and POST /upload routes
└── ENGINEERING_STANDARDS.md         # Architecture and invariants reference
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/dexterouspuma/sop-creator.git
cd sop-creator
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt --only-binary=:all:
```

> The `--only-binary` flag is required on Python 3.13 to avoid C++ compilation errors for `lxml` and `PyMuPDF`.

### 4. Configure environment variables

Copy the example file to create your own `.env`:

```bash
# Windows (PowerShell)
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Open `.env` and replace the placeholder values with your actual Azure details:

```env
AZURE_AIPROJECT_ENDPOINT=https://{your-resource}.services.ai.azure.com/api/projects/{your-project}
AI_MODEL=gpt-4.1-mini
APP_ENV=development
```

> Find your endpoint in [Azure AI Foundry](https://ai.azure.com) under your project → Overview → Endpoint.
> Find available model deployment names under your project → Deployments.

### 5. Log into Azure

```bash
az login
```

The app uses `DefaultAzureCredential` — no API key needed, just an active Azure CLI session.
Run `az login` once per session before starting the app.

### 6. Run the app

Make sure your virtual environment is activated first, then start the server:

```bash
# Windows (PowerShell)
venv\Scripts\activate
uvicorn main:app --reload

# Mac / Linux
source venv/bin/activate
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

> `--reload` automatically restarts the server when you save a file. Remove it in production.

---

## How It Works

1. User uploads a file via the form
2. The extractor converts it to ordered content blocks (text + images in document order)
3. Blocks are sent to Azure AI with a structured prompt
4. Claude returns a formatted SOP (TITLE / OVERVIEW / STEPS)
5. The parser converts the response into a Python dict
6. Jinja2 renders the result as an HTML fragment
7. HTMX swaps the fragment into the page — no full reload
8. User can edit any field inline, then download as PDF or copy as text

---

## Supported File Types

| Format | Text | Embedded Images |
|---|---|---|
| PDF | Extracted via PyMuPDF (falls back to vision for scanned PDFs) | Included natively |
| DOCX | python-docx extracts text | Extracted from ZIP in document order |
| XLSX | openpyxl extracts cells sheet by sheet | Extracted from ZIP |
| PNG / JPG / GIF / WebP | — | Sent directly as base64 |
| TXT | Sent as-is | — |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `AZURE_AIPROJECT_ENDPOINT` | Yes | — | Azure AI Foundry project endpoint |
| `AI_MODEL` | No | `gpt-4o` | Model deployment name in your Azure project |
| `APP_ENV` | No | `development` | `development` or `production` |
