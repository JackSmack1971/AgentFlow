import os
from r2r import R2RClient

def make_client() -> R2RClient:
    base = os.getenv("R2R_BASE_URL", "http://localhost:7272")
    api_key = os.getenv("R2R_API_KEY")
    if api_key:
        os.environ["R2R_API_KEY"] = api_key
        return R2RClient()
    return R2RClient(base_url=base)
