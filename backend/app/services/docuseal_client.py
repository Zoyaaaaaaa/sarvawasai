import os
import json
from typing import Any, Dict, List, Optional, Tuple
import requests
import dotenv   
dotenv.load_dotenv()

class DocuSealError(Exception):
    pass

class DocuSealClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = (api_key or os.getenv("DOCUSEAL_API_KEY", "")).strip().strip('"').strip("'")
        raw_base = (base_url or os.getenv("DOCUSEAL_BASE_URL", "https://api.docuseal.com")).strip()
        # Remove accidental surrounding quotes from env like "https://..."
        if (raw_base.startswith('"') and raw_base.endswith('"')) or (raw_base.startswith("'") and raw_base.endswith("'")):
            raw_base = raw_base[1:-1]
        b = raw_base.rstrip("/")
        # Normalize base URL: append '/api' only when not using the 'api.' subdomain
        try:
            lower = b.lower()
            if "docuseal.com" in lower and not lower.startswith("https://api.") and not b.endswith("/api"):
                b = f"{b}/api"
        except Exception:
            pass
        self.base_url = b
        if not self.api_key:
            raise DocuSealError("DOCUSEAL_API_KEY not configured")

    def _headers(self) -> Dict[str, str]:
        # DocuSeal uses X-Auth-Token
        return {
            "X-Auth-Token": self.api_key,
            "Accept": "application/json",
        }

    def create_submission(self, template_id: int, submitters: List[Dict[str, Any]], send_email: bool = False, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/submissions"
        data = {"template_id": template_id, "submitters": submitters, "send_email": send_email}
        if extra:
            data.update(extra)
        r = requests.post(url, json=data, headers=self._headers(), timeout=30)
        if r.status_code >= 400:
            raise DocuSealError(f"POST {url} -> {r.status_code}: {r.text}")
        return r.json()

    def update_submitter(self, submitter_id: int | str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PUT /submitters/{id}
        Useful for auto-completing a submitter or updating their fields.
        """
        url = f"{self.base_url}/submitters/{submitter_id}"
        r = requests.put(url, json=data, headers=self._headers(), timeout=30)
        if r.status_code >= 400:
            raise DocuSealError(f"PUT {url} -> {r.status_code}: {r.text}")
        return r.json()

    def create_submission_from_pdf(
        self,
        pdf_bytes: bytes,
        submitters: List[Dict[str, Any]],
        fields: List[Dict[str, Any]],
        send_email: bool = False,
        filename: str = "agreement.pdf",
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        POST /submissions/pdf (JSON)
        - documents: [{ name, file: base64, fields }]
        - submitters: array
        - send_email: bool
        """
        url = f"{self.base_url}/submissions/pdf"
        # Base64-encode PDF for JSON API
        import base64
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        doc_name = filename or "agreement.pdf"

        payload: Dict[str, Any] = {
            "send_email": bool(send_email),
            "documents": [
                {
                    "name": doc_name,
                    "file": pdf_b64,
                    "fields": fields or [],
                }
            ],
            "submitters": submitters or [],
        }
        if extra and isinstance(extra, dict):
            # Include only JSON-serializable keys
            for k, v in extra.items():
                payload[k] = v

        r = requests.post(url, json=payload, headers=self._headers(), timeout=60)
        if r.status_code >= 400:
            raise DocuSealError(f"POST {url} -> {r.status_code}: {r.text}")
        return r.json()

    def get_submission(self, submission_id: int) -> Dict[str, Any]:
        url = f"{self.base_url}/submissions/{submission_id}"
        r = requests.get(url, headers=self._headers(), timeout=30)
        if r.status_code >= 400:
            raise DocuSealError(f"GET {url} -> {r.status_code}: {r.text}")
        return r.json()

    def download_file(self, url: str) -> Tuple[bytes, str]:
        r = requests.get(url, headers=self._headers(), timeout=120)
        if r.status_code >= 400:
            raise DocuSealError(f"GET {url} -> {r.status_code}: {r.text}")
        content_type = r.headers.get("Content-Type", "application/octet-stream")
        return r.content, content_type
