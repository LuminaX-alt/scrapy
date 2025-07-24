import warnings
from OpenSSL import SSL
from twisted.internet._sslverify import ClientTLSOptions
from twisted.internet.ssl import CertificateOptions

from scrapy import twisted_version
from scrapy.utils.python import to_bytes


class ScrapyClientContextFactory:
    def __init__(self, method=SSL.SSLv23_METHOD, alpn_protos=None, cipher_list=None):
        self.method = method
        self._alpn_protos = alpn_protos or []
        self._cipher_list = cipher_list or "DEFAULT"

    def getContext(self):
        """
        Create and configure the SSL context at initialization time.
        This avoids mutating the context after a connection is created,
        preventing DeprecationWarnings in pyOpenSSL >= 25.1.0.
        """
        ctx = SSL.Context(self.method)
        try:
            if self._alpn_protos:
                ctx.set_alpn_protos([to_bytes(p) for p in self._alpn_protos])
        except Exception as e:
            warnings.warn(f"Failed to set ALPN protocols: {e}", RuntimeWarning)
        try:
            if self._cipher_list:
                ctx.set_cipher_list(to_bytes(self._cipher_list))
        except Exception as e:
            warnings.warn(f"Failed to set cipher list: {e}", RuntimeWarning)
        return ctx


class ScrapyClientTLSOptions(ClientTLSOptions):
    """
    Custom TLS options that ensure no Context mutations happen after
    a Connection has been created. Extra certificates are added before
    the connection to prevent pyOpenSSL 25.1.0 warnings.
    """
    def __init__(self, hostname, ctx, extra_cert_chain=None):
        # Add extra certs before connection creation
        if extra_cert_chain:
            for cert in extra_cert_chain:
                ctx.add_extra_chain_cert(cert)
        super().__init__(hostname, ctx)
