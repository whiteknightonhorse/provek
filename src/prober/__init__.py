"""Prober: the one active operation this repository can perform, and it is fail-closed.

`src/mandate` decides WHETHER we may touch a live system. This package is the thing that would do
the touching, and until it existed the mandate object governed nothing - the intake was right to
withdraw the offer (D-21). One action is implemented, named `unauthenticated_access_attempt`, and
the mandate is checked before any call leaves this process.
"""
