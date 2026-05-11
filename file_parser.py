"""Extract plain text from uploaded PDF, DOCX, or TXT files."""
import io
import pdfplumber
import docx as python_docx


def extract_text(filename: str, content: bytes) -> str:
    name = filename.lower()
    if name.endswith(".pdf"):
        return _from_pdf(content)
    elif name.endswith(".docx"):
        return _from_docx(content)
    elif name.endswith(".txt"):
        return content.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {filename}. Upload PDF, DOCX, or TXT.")


def _from_pdf(content: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts).strip()


def _from_docx(content: bytes) -> str:
    doc = python_docx.Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
