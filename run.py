#!/usr/bin/env python3
"""Start HireAI — runs HTTP on :8000 (admin) and HTTPS on :8443 (LAN candidates)."""
import sys
import os
import asyncio
import socket
import ipaddress
import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from config import HOST, PORT, GROQ_API_KEY

if not GROQ_API_KEY:
    print("\n⚠️  GROQ_API_KEY is not set.")
    print("   1. Go to https://console.groq.com  (free signup)")
    print("   2. Create an API key")
    print("   3. Add it to your .env: GROQ_API_KEY=gsk_...")
    sys.exit(1)

import uvicorn

HTTPS_PORT = 8443
CERT_FILE  = Path(__file__).parent / "ssl_cert.pem"
KEY_FILE   = Path(__file__).parent / "ssl_key.pem"


def _local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _generate_ssl_cert(lan_ip: str) -> bool:
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        print("   🔐 Generating self-signed SSL certificate…", flush=True)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        san = [x509.DNSName("localhost"), x509.IPAddress(ipaddress.IPv4Address("127.0.0.1"))]
        try:
            san.append(x509.IPAddress(ipaddress.IPv4Address(lan_ip)))
        except Exception:
            pass

        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "HireAI Local")])
        cert = (
            x509.CertificateBuilder()
            .subject_name(name).issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
            .add_extension(x509.SubjectAlternativeName(san), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )
        CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        KEY_FILE.write_bytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ))
        print("   ✅ SSL certificate ready.", flush=True)
        return True
    except Exception as e:
        print(f"   ⚠️  SSL cert generation failed: {e}", flush=True)
        return False


async def _serve():
    # HTTP server — admin on localhost (localhost is a secure context for camera/mic)
    http_cfg = uvicorn.Config(
        "api:app", host=HOST, port=PORT,
        log_level="info", lifespan="on",
    )
    # HTTPS server — candidates on LAN / other devices (camera/mic requires HTTPS)
    https_cfg = uvicorn.Config(
        "api:app", host=HOST, port=HTTPS_PORT,
        ssl_certfile=str(CERT_FILE), ssl_keyfile=str(KEY_FILE),
        log_level="warning", lifespan="on",
    )

    http_server  = uvicorn.Server(http_cfg)
    https_server = uvicorn.Server(https_cfg)

    # Let asyncio.gather handle signals cleanly
    http_server.install_signal_handlers  = lambda: None
    https_server.install_signal_handlers = lambda: None

    await asyncio.gather(http_server.serve(), https_server.serve())


if __name__ == "__main__":
    lan_ip = _local_ip()

    # Generate SSL cert if missing or expired
    need_cert = not (CERT_FILE.exists() and KEY_FILE.exists())
    if not need_cert:
        age = (datetime.datetime.utcnow() -
               datetime.datetime.utcfromtimestamp(CERT_FILE.stat().st_mtime)).days
        need_cert = age > 800
    if need_cert:
        _generate_ssl_cert(lan_ip)

    ssl_ok = CERT_FILE.exists() and KEY_FILE.exists()

    print(f"\n🤖  HireAI  (Groq + Llama 3.3 70B)\n")
    print(f"   Admin Dashboard   →  http://localhost:{PORT}")
    print(f"   Admin (LAN)       →  http://{lan_ip}:{PORT}")
    if ssl_ok:
        print(f"\n   Candidate Links   →  https://{lan_ip}:{HTTPS_PORT}  ← camera/mic works here")
        print(f"   ⚠️  First visit: click  Advanced → Proceed  to bypass SSL warning")
    print(f"\n   API Docs          →  http://localhost:{PORT}/docs")
    print(f"   Public HTTPS URL  →  python start_public.py")
    print()

    try:
        asyncio.run(_serve())
    except KeyboardInterrupt:
        print("\n⏹  Server stopped.")
