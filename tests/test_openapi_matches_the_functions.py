"""/openapi.json is generated from the routes the site really serves, and is bound to the Function
tree by this file (T-AEO-03, PROVEK-AEO-1110 ruling-1 item 4, D-83).

WHY THIS EXISTS. A description of an API that nothing holds to the code is the second copy this
project forbids: it is true on the day it is written. Every check below is a comparison of the
document against the SOURCE it describes, in both directions where there are two sets, and each
comparison is a function over (functions root, document) so the mutation tests at the end can run
the very same function over a doctored copy and show it go red (invariant 5).

  paths     == routes derived from the web/functions file tree + the two static /data paths
  methods   == the exported `onRequest<Method>` handlers of each file
  statuses  == the status literals of the three api handlers (and witnessRelay.js)
  no security scheme anywhere (auth.md says "Authentication: none")
  checked-in web/public/openapi.json == a fresh run of web/openapi.mjs; web/dist copy byte-identical
"""
from __future__ import annotations

import copy
import json
import pathlib
import re
import shutil
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
FUNCTIONS = WEB / "functions"
CHECKED_IN = WEB / "public" / "openapi.json"
BUILT = WEB / "dist" / "openapi.json"
SITE = "https://provek.dev"

STATIC_PATHS = {"/data/registry.json", "/data/passports/{slug}.json"}
# Documented in the document, produced by the Cloudflare edge and by no handler source.
EDGE_STATUSES = {("/api/apply", "429")}
API_FILES = {
    "/api/apply": ["api/apply.js"],
    "/api/apply/{}": ["api/apply/[id].js"],
    "/api/witness-submit": ["api/witness-submit.js", "_lib/witnessRelay.js"],
}
METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def generate() -> dict:
    r = subprocess.run(["node", str(WEB / "openapi.mjs"), SITE], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"openapi.mjs failed: {r.stderr}"
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def doc() -> dict:
    return generate()


def norm(path: str) -> str:
    """A templated segment, with any suffix after it (`{slug}.svg`), is one `{}`."""
    return re.sub(r"\{[^}]+\}(\.\w+)?", "{}", path)


# --------------------------------------------------------------------------------- derivations

def routes_from_tree(root: pathlib.Path) -> dict[str, pathlib.Path]:
    """`{route: file}` from the Pages Functions file tree. Files and directories starting with `_`
    are not routes; `[id]` is one templated segment."""
    out = {}
    for f in sorted(root.rglob("*.js")):
        rel = f.relative_to(root)
        if any(part.startswith("_") for part in rel.parts):
            continue
        parts = list(rel.parts)
        parts[-1] = parts[-1][:-3]
        if parts[-1] == "index":
            parts.pop()
        out["/" + "/".join("{}" if re.fullmatch(r"\[[^\]]+\]", p) else p for p in parts)] = f
    return out


def exported_methods(src: str) -> set[str]:
    return {m.lower() for m in re.findall(
        r"export\s+(?:async\s+function|const)\s+onRequest(Get|Post|Put|Patch|Delete|Head|Options)\b", src)}


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(^|\s)//[^\n]*", r"\1", src)


def status_literals(src: str) -> set[str]:
    """Status codes a handler source can answer: `status: N`, `status = N`, a trailing `, N)`/`, N,`
    argument (2xx, 4xx, 5xx - no handler redirects), and 200 for a `Response.json(...)` with no status."""
    code = strip_comments(src)
    found = set(re.findall(r"status\s*[:=]\s*(\d{3})\b", code))
    found |= set(re.findall(r",\s*([245]\d\d)\s*[,)]", code))
    for stmt in re.findall(r"Response\.json\([^;]*;", code):
        if "status" not in stmt:
            found.add("200")
    return found


def documented_statuses(document: dict, route: str) -> set[str]:
    codes = set()
    for p, item in document["paths"].items():
        if norm(p) != route:
            continue
        for m, op in item.items():
            if m in METHODS or m == "x-any-other-method":   # the latter: a file's catch-all `onRequest`
                codes |= {c for c in op["responses"] if (p, c) not in EDGE_STATUSES or m != "post"}
    return codes


# --------------------------------------------------------------------------------- checks

def path_problems(root: pathlib.Path, document: dict) -> list[str]:
    want = {norm(r) for r in routes_from_tree(root)} | {norm(p) for p in STATIC_PATHS}
    got = {norm(p) for p in document["paths"]}
    return ([f"function file with no documented path: {r}" for r in sorted(want - got)] +
            [f"documented path with no function file: {r}" for r in sorted(got - want)])


def method_problems(root: pathlib.Path, document: dict) -> list[str]:
    out = []
    for route, f in routes_from_tree(root).items():
        want = exported_methods(f.read_text(encoding="utf-8"))
        got = set()
        for p, item in document["paths"].items():
            if norm(p) == route:
                got |= {m for m in item if m in METHODS}
        if want != got:
            out.append(f"{route}: handlers {sorted(want)} != documented {sorted(got)}")
    return out


def status_problems(root: pathlib.Path, document: dict) -> list[str]:
    out = []
    for route, files in API_FILES.items():
        src = "\n".join((root / f).read_text(encoding="utf-8") for f in files)
        want, got = status_literals(src), documented_statuses(document, route)
        if want != got:
            out.append(f"{route}: source {sorted(want)} != documented {sorted(got)}")
    return out


def find_key(node, names) -> list[str]:
    hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in names:
                hits.append(k)
            hits += find_key(v, names)
    elif isinstance(node, list):
        for v in node:
            hits += find_key(v, names)
    return hits


# --------------------------------------------------------------------------------- tests

def test_openapi_version_is_3_1(doc):
    assert re.fullmatch(r"3\.1\.\d+", doc["openapi"]), doc["openapi"]
    assert doc["servers"] == [{"url": SITE}]


def test_the_path_set_is_the_function_tree_plus_the_two_data_paths(doc):
    assert path_problems(FUNCTIONS, doc) == []


def test_the_seven_paths_are_the_ones_the_ruling_names(doc):
    assert sorted(doc["paths"]) == sorted([
        "/data/registry.json", "/data/passports/{slug}.json", "/api/apply", "/api/apply/{id}",
        "/api/witness-submit", "/badge/{slug}.svg", "/p/{slug}/brief"])


def test_methods_per_path_are_the_exported_handlers(doc):
    assert method_problems(FUNCTIONS, doc) == []


def test_documented_status_codes_are_the_status_literals_of_the_api_handlers(doc):
    assert status_problems(FUNCTIONS, doc) == []


def test_every_operation_has_a_response_and_every_response_a_description(doc):
    for p, item in doc["paths"].items():
        for m, op in item.items():
            assert op["responses"], (p, m)
            for c, r in op["responses"].items():
                assert r.get("description"), (p, m, c)


def test_no_security_scheme_anywhere(doc):
    assert find_key(doc, {"securitySchemes", "security"}) == []
    assert '"securitySchemes"' not in CHECKED_IN.read_text(encoding="utf-8")


def test_limits_criteria_and_consent_version_are_the_modules_own(doc):
    s = doc["components"]["schemas"]
    src = (FUNCTIONS / "_lib" / "witnessRelay.js").read_text(encoding="utf-8")
    lim = dict(re.findall(r"(per_ip_per_hour|per_day_global):\s*(\d+)", src))
    assert {k: v["const"] for k, v in s["WitnessRelayStatus"]["properties"]["limits"]["properties"].items()} == \
        {k: int(v) for k, v in lim.items()}
    crit = re.search(r"CRITERIA\s*=\s*Object\.freeze\(\[([^\]]*)\]", src).group(1)
    assert s["WitnessRequest"]["properties"]["criterion"]["enum"] == re.findall(r'"([^"]+)"', crit)
    apply_src = (FUNCTIONS / "api" / "apply.js").read_text(encoding="utf-8")
    assert s["ApplyRequest"]["properties"]["consent_version"]["const"] == \
        re.search(r'CONSENT_VERSION\s*=\s*"([^"]+)"', apply_src).group(1)
    assert str(s["ApplyRequest"]["properties"]["contact"]["maxLength"]) == \
        re.search(r"CONTACT_MAX\s*=\s*(\d+)", apply_src).group(1)
    assert str(re.search(r"MAX_BODY_BYTES\s*=\s*(\d+)", src).group(1)) in \
        doc["paths"]["/api/witness-submit"]["post"]["description"]


def test_literals_a_module_does_not_export_are_read_from_the_source(doc):
    """The numbers openapi.mjs states itself are compared with the source that holds them."""
    src = (FUNCTIONS / "_lib" / "witnessRelay.js").read_text(encoding="utf-8")
    w = doc["components"]["schemas"]["WitnessRequest"]["properties"]
    assert w["subject_id"]["maxLength"] == int(re.search(r"chars\(subject_id\)\s*>\s*(\d+)", src).group(1))
    assert w["evidence_url"]["maxLength"] == int(re.search(r"chars\(url\)\s*>\s*(\d+)", src).group(1))
    ident = (FUNCTIONS / "api" / "apply" / "[id].js").read_text(encoding="utf-8")
    fn = ident[ident.index("function stateOf"):ident.index("function registryUrl")]
    states = [s for s in re.findall(r'return "(\w+)"', fn)]
    desc = doc["components"]["schemas"]["ApplyStatus"]["properties"]["state"]["description"]
    assert states and all(s in desc for s in states), (states, desc)
    lookup = set(re.findall(r'state:\s*"(\w+)"\s*\}', ident)) - set(states)
    assert set(doc["components"]["schemas"]["ApplyLookupFailure"]["properties"]["state"]["enum"]) == lookup
    apply_tsx = (WEB / "src" / "pages" / "Apply.tsx").read_text(encoding="utf-8")
    m = re.search(r"\((\d+) per (\d+) s per IP", apply_tsx)
    post = doc["paths"]["/api/apply"]["post"]["description"]
    assert f"({m.group(1)} per {m.group(2)} s)" in post


def test_checked_in_file_is_a_fresh_generator_run(doc):
    assert CHECKED_IN.read_text(encoding="utf-8") == json.dumps(doc, indent=2) + "\n"


def test_built_openapi_is_byte_identical_to_the_source():
    assert BUILT.is_file(), f"{BUILT} is absent: run `npm run build` in web/ (push.sh does)"
    assert BUILT.read_bytes() == CHECKED_IN.read_bytes()


def test_headers_serve_openapi_as_json_cors_open():
    text = (WEB / "public" / "_headers").read_text(encoding="utf-8")
    block = re.search(r"^/openapi\.json\n((?:  .+\n)+)", text, re.M)
    assert block, "/openapi.json has no _headers block"
    assert "Content-Type: application/json" in block.group(1)
    assert "Access-Control-Allow-Origin: *" in block.group(1)


# --------------------------------------------------------------------------------- mutation proofs

def _functions_copy(tmp_path: pathlib.Path) -> pathlib.Path:
    dst = tmp_path / "functions"
    shutil.copytree(FUNCTIONS, dst)
    return dst


def test_checks_are_green_on_the_real_tree_before_any_mutation(doc, tmp_path):
    root = _functions_copy(tmp_path)
    assert path_problems(root, doc) == method_problems(root, doc) == status_problems(root, doc) == []


def test_an_added_stub_function_file_turns_the_path_check_red(doc, tmp_path):
    root = _functions_copy(tmp_path)
    (root / "api" / "stub.js").write_text("export const onRequestGet = () => new Response('x', { status: 200 });\n")
    problems = path_problems(root, doc)
    assert problems == ["function file with no documented path: /api/stub"], problems
    assert method_problems(root, doc), "the stub's handler is undocumented, the method check must see it too"


def test_a_removed_status_code_turns_the_status_check_red(doc, tmp_path):
    mutated = copy.deepcopy(doc)
    del mutated["paths"]["/api/witness-submit"]["post"]["responses"]["502"]
    assert status_problems(FUNCTIONS, mutated), "dropping 502 from the document did not register"
    mutated = copy.deepcopy(doc)
    del mutated["paths"]["/api/apply/{id}"]["get"]["responses"]["500"]
    assert status_problems(FUNCTIONS, mutated)


def test_an_added_status_in_a_handler_turns_the_status_check_red(doc, tmp_path):
    root = _functions_copy(tmp_path)
    f = root / "api" / "apply" / "[id].js"
    f.write_text(f.read_text(encoding="utf-8").replace('"status_unavailable" }, 503);', '"status_unavailable" }, 504);', 1))
    assert status_problems(root, doc)


def test_a_path_with_no_file_turns_the_path_check_red(doc):
    mutated = copy.deepcopy(doc)
    mutated["paths"]["/api/ghost"] = {"get": {"responses": {"200": {"description": "x"}}}}
    assert path_problems(FUNCTIONS, mutated) == ["documented path with no function file: /api/ghost"]


def test_a_security_scheme_would_be_found(doc):
    mutated = copy.deepcopy(doc)
    mutated["components"]["securitySchemes"] = {"k": {"type": "apiKey"}}
    assert find_key(mutated, {"securitySchemes", "security"}) == ["securitySchemes"]
