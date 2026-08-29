from google.oauth2.credentials import Credentials

c = Credentials(token="x", refresh_token=None, client_id="i", client_secret="s")
print("expired:", c.expired, "| valid:", c.valid)

from unittest.mock import MagicMock
from googleapiclient.errors import HttpError

resp = MagicMock()
resp.status = 403
resp.reason = "Forbidden"
resp.get = MagicMock(return_value=None)
e = HttpError(resp, b"bad")
print("http_err status:", e.resp.status)
print("PROBE_OK")
