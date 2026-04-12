import hashlib
import os
import requests
from typing import Optional, Dict, Any
import dotenv
dotenv.load_dotenv()

class IPFSClient:
    """
    Pinata-only IPFS uploader.
    Configure via env:
      - PINATA_JWT or PINATA_API_KEY + PINATA_API_SECRET
      - IPFS_GATEWAY (optional, default https://ipfs.io/ipfs)
    """

    def __init__(self, gateway: Optional[str] = None):
        self.gateway = (gateway or os.getenv("IPFS_GATEWAY") or "https://ipfs.io/ipfs").rstrip("/")

    @staticmethod
    def sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def upload_bytes(self, data: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        return self._upload_pinata(data, filename)

    def _upload_pinata(self, data: bytes, filename: str) -> Dict[str, Any]:
        jwt = os.getenv("PINATA_JWT")
        api_key = os.getenv("PINATA_API_KEY")
        api_secret = os.getenv("PINATA_API_SECRET")
        headers = {}
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"
        elif api_key and api_secret:
            headers["pinata_api_key"] = api_key
            headers["pinata_secret_api_key"] = api_secret
        else:
            raise RuntimeError("Missing PINATA_JWT or PINATA_API_KEY/PINATA_API_SECRET for Pinata")

        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        files = {
            "file": (filename, data, "application/pdf"),
        }
        resp = requests.post(url, headers=headers, files=files, timeout=120)
        resp.raise_for_status()
        body = resp.json()
        cid = body.get("IpfsHash") or body.get("Hash")
        if not cid:
            raise RuntimeError(f"Unexpected Pinata response: {body}")
        sha = self.sha256(data)
        return {
            "provider": "pinata",
            "cid": cid,
            "sha256": sha,
            "size": len(data),
            "gateway_url": f"{self.gateway}/{cid}",
        }
