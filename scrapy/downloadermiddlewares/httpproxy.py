import base64
from urllib.parse import urlparse
from scrapy.exceptions import NotConfigured

class HttpProxyMiddleware:
    def __init__(self, settings):
        self.auth_encoding = settings.get('HTTPPROXY_AUTH_ENCODING') or 'latin-1'

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.get('HTTPPROXY_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings)

    def update_proxy_auth(self, request):
        """
        Refresh proxy authentication for a request.
        Called right before the request is downloaded.
        """
        proxy_url = request.meta.get("proxy")
        if not proxy_url:
            return
        parsed = urlparse(proxy_url)
        if parsed.username and parsed.password:
            creds = f"{parsed.username}:{parsed.password}"
            request.headers["Proxy-Authorization"] = b"Basic " + base64.b64encode(
                creds.encode(self.auth_encoding)
            )
username)}:{unquote(password)}", encoding=self.auth_encoding
        )
        return base64.b64encode(user_pass)

    def _get_proxy(self, url: str, orig_type: str) -> tuple[bytes | None, str]:
        proxy_type, user, password, hostport = _parse_proxy(url)
        proxy_url = urlunparse((proxy_type or orig_type, hostport, "", "", "", ""))

        creds = self._basic_auth_header(user, password) if user else None

        return creds, proxy_url

    def process_request(
        self, request: Request, spider: Spider
    ) -> Request | Response | None:
        creds, proxy_url, scheme = None, None, None
        if "proxy" in request.meta:
            if request.meta["proxy"] is not None:
                creds, proxy_url = self._get_proxy(request.meta["proxy"], "")
        elif self.proxies:
            parsed = urlparse_cached(request)
            _scheme = parsed.scheme
            if (
                # 'no_proxy' is only supported by http schemes
                _scheme not in ("http", "https")
                or (parsed.hostname and not proxy_bypass(parsed.hostname))
            ) and _scheme in self.proxies:
                scheme = _scheme
                creds, proxy_url = self.proxies[scheme]

        self._set_proxy_and_creds(request, proxy_url, creds, scheme)
        return None

    def _set_proxy_and_creds(
        self,
        request: Request,
        proxy_url: str | None,
        creds: bytes | None,
        scheme: str | None,
    ) -> None:
        if scheme:
            request.meta["_scheme_proxy"] = True
        if proxy_url:
            request.meta["proxy"] = proxy_url
        elif request.meta.get("proxy") is not None:
            request.meta["proxy"] = None
        if creds:
            request.headers[b"Proxy-Authorization"] = b"Basic " + creds
            request.meta["_auth_proxy"] = proxy_url
        elif "_auth_proxy" in request.meta:
            if proxy_url != request.meta["_auth_proxy"]:
                if b"Proxy-Authorization" in request.headers:
                    del request.headers[b"Proxy-Authorization"]
                del request.meta["_auth_proxy"]
        elif b"Proxy-Authorization" in request.headers:
            if proxy_url:
                request.meta["_auth_proxy"] = proxy_url
            else:
                del request.headers[b"Proxy-Authorization"]
