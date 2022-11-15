import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import http


# Set the timeout for HTTP requests
DEFAULT_TIMEOUT = 5 # seconds

# Set the level of detail for HTTP debug info in the console
HTTP_DEBUG_LEVEL = 0

# Retry strategy
retries = Retry(total=1, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])

# Create a custom requests object
http_client = requests.Session()

# Set the debug level
http.client.HTTPConnection.debuglevel = HTTP_DEBUG_LEVEL

# Call back if the server responds with an HTTP error code
assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
http_client.hooks["response"] = [assert_status_hook]

# Extend the HTTP adapter so that it provides a default timeout that you can override when constructing the client
class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)
    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)

# Mount the extended timeout adaptor with the retry strategy for all requests
http_client.mount("https://", TimeoutHTTPAdapter(max_retries=retries))
http_client.mount("http://", TimeoutHTTPAdapter(max_retries=retries))