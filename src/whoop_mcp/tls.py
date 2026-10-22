"""Use native OS trust, including locally administered trust anchors; never disable TLS."""

import ssl

import truststore


def context():
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
