"""Regression for the SPA fallback path traversal (main.py serve_spa).

Reproduces the real exploit reported against the running instance:
    curl --path-as-is http://.../../../../etc/hostname   -> leaked /etc/hostname
    curl --path-as-is http://.../../data/animehub.db     -> leaked the DB file

serve_spa must stay inside STATIC_DIR (via safe_path.resolve_inside) and keep
serving index.html for unknown frontend routes (SPA client-side routing).
"""
import asyncio

from app.main import STATIC_DIR, serve_spa

INDEX = STATIC_DIR / "index.html"


def test_dotdot_traversal_does_not_escape_static_dir():
    response = asyncio.run(serve_spa(None, "../../../../etc/hostname"))
    # Falls back to index.html, never serves the escaped file.
    assert str(response.path) == str(INDEX)


def test_traversal_to_sibling_db_file_does_not_escape():
    response = asyncio.run(serve_spa(None, "../data/animehub.db"))
    assert str(response.path) == str(INDEX)


def test_unknown_frontend_route_falls_back_to_index_html():
    response = asyncio.run(serve_spa(None, "anime/some-unknown-route"))
    assert str(response.path) == str(INDEX)
