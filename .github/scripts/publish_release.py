"""Publish a complete, verified draft before moving the public latest link."""
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
import zipfile


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def verify(root):
    root = Path(root).resolve()
    plan = json.loads((root / "publication/release.json").read_text(encoding="utf-8"))
    if plan.get("schema") != 1 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", plan["tag"]):
        raise ValueError("Invalid release descriptor")
    assets = []
    names = set()
    for item in plan["assets"]:
        path = (root / item["path"]).resolve()
        path.relative_to(root / "downloads")
        if path.name != item["name"] or path.name in names:
            raise ValueError("Invalid or duplicate asset name")
        if path.stat().st_size != item["size"] or digest(path) != item["sha256"]:
            raise ValueError("Asset checksum mismatch: " + item["name"])
        names.add(path.name)
        assets.append((item, path))
    by_name = {item["name"]: path for item, path in assets}
    catalog = json.loads(by_name["catalog.json"].read_text(encoding="utf-8"))
    if catalog.get("schema") != 1 or len(catalog.get("mods", [])) != 4:
        raise ValueError("The four mods must be included")
    identifiers = set()
    expected = {"mr14karaecu", "mr14karaairsuspension", "mr14karadieselsmoke", "volumetricbackfire"}
    for mod in catalog["mods"]:
        identifiers.add(mod["id"])
        prefix = "https://github.com/" + plan["repository"] + "/releases/download/" + plan["tag"] + "/"
        if not mod["url"].startswith(prefix):
            raise ValueError("A mod does not point to this immutable release")
        path = by_name[mod["url"][len(prefix):]]
        if path.stat().st_size != mod["size"] or digest(path) != mod["sha256"]:
            raise ValueError("Catalogue checksum mismatch")
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError("Damaged mod ZIP")
            info = json.loads(archive.read("mod_info/" + mod["id"] + "/info.json"))
            if info["version"] != mod["version"]:
                raise ValueError("Wrong mod version")
    if identifiers != expected:
        raise ValueError("Unexpected mod identifiers")
    with zipfile.ZipFile(by_name[plan["application"]]) as archive:
        if archive.testzip() is not None:
            raise ValueError("Damaged Windows application")
        channel = json.loads(archive.read("Mr14KaraFR-Mod-Center/_internal/channel.json"))
        if channel["catalog_url"] != "https://github.com/" + plan["repository"] + "/releases/latest/download/catalog.json":
            raise ValueError("Application update channel mismatch")
    applications = catalog.get("applications", [])
    if {app["id"] for app in applications} != {"modcenter", "ecustudio"} or len(applications) != 2:
        raise ValueError("Both Windows applications must be included")
    executables = {"modcenter": "Mr14KaraFR-Mod-Center.exe", "ecustudio": "ECU-Studio.exe"}
    for app in applications:
        prefix = "https://github.com/" + plan["repository"] + "/releases/download/" + plan["tag"] + "/"
        if not app["url"].startswith(prefix):
            raise ValueError("Application URL must point to this release")
        path = by_name[app["url"][len(prefix):]]
        if path.stat().st_size != app["size"] or digest(path) != app["sha256"]:
            raise ValueError("Application checksum mismatch")
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise ValueError("Damaged application ZIP")
            manifest = json.loads(archive.read("application.json"))
            if manifest != {"id": app["id"], "version": app["version"], "executable": executables[app["id"]]}:
                raise ValueError("Application identity/version mismatch")
            if executables[app["id"]] not in archive.namelist():
                raise ValueError("Application executable missing")
    if "catalog-beta.json" in by_name:
        beta = json.loads(by_name["catalog-beta.json"].read_text(encoding="utf-8"))
        if beta.get("schema") != 1 or beta.get("channel") != "beta" or not beta.get("mods"):
            raise ValueError("Invalid beta catalogue")
        auth = channel.get("discord_auth", {})
        expected_beta = "https://github.com/" + plan["repository"] + "/releases/latest/download/catalog-beta.json"
        if not auth.get("enabled") or not auth.get("beta_role_id") or auth.get("beta_catalog_url") != expected_beta:
            raise ValueError("Compiled application does not configure the beta role/catalogue")
        for mod in beta["mods"]:
            prefix = "https://github.com/" + plan["repository"] + "/releases/download/" + plan["tag"] + "/"
            if mod.get("access") != "beta" or mod["id"] not in expected or not mod["url"].startswith(prefix):
                raise ValueError("Invalid beta download or role")
            path = by_name[mod["url"][len(prefix):]]
            if path.stat().st_size != mod["size"] or digest(path) != mod["sha256"]:
                raise ValueError("Beta checksum mismatch")
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise ValueError("Damaged beta ZIP")
                info = json.loads(archive.read("mod_info/" + mod["id"] + "/info.json"))
                if info["version"] != mod["version"]:
                    raise ValueError("Wrong beta mod version")
            if any(stable["id"] == mod["id"] and stable["version"] == mod["version"] for stable in catalog["mods"]):
                raise ValueError("Beta version must not be advertised in stable catalogue")
    return plan, assets


def publish(root):
    plan, assets = verify(root)
    repo = os.environ["GITHUB_REPOSITORY"]
    if repo != plan["repository"]:
        raise ValueError("Publication is restricted to the configured repository")
    headers = {"Authorization": "Bearer " + os.environ["GH_TOKEN"],
               "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    def api(path, data=None, method=None):
        request = Request("https://api.github.com/repos/" + repo + path,
                          data=json.dumps(data).encode() if data is not None else None,
                          headers={**headers, "Content-Type": "application/json"}, method=method)
        with urlopen(request, timeout=60) as response:
            return json.load(response)
    try:
        release = api("/releases/tags/" + quote(plan["tag"], safe=""))
    except HTTPError as exc:
        if exc.code != 404:
            raise
        release = api("/releases", dict(tag_name=plan["tag"], target_commitish=os.environ["GITHUB_SHA"],
                                       name=plan["title"], body=plan["notes"], draft=True, prerelease=False))
    remote_assets = {asset["name"]: asset for asset in release["assets"]}
    for item, path in assets:
        existing = remote_assets.get(item["name"])
        if existing:
            if existing["size"] != item["size"] or existing.get("digest") not in (None, "sha256:" + item["sha256"]):
                raise ValueError("An existing remote asset differs; nothing will be overwritten")
            continue
        if not release["draft"]:
            raise ValueError("A published release is immutable; choose a new tag")
        upload = release["upload_url"].split("{", 1)[0] + "?name=" + quote(item["name"])
        if urlsplit(upload).hostname != "uploads.github.com":
            raise ValueError("Unexpected upload host")
        request = Request(upload, data=path.read_bytes(),
                          headers={**headers, "Content-Type": "application/octet-stream"})
        with urlopen(request, timeout=120) as response:
            created = json.load(response)
        if created["size"] != item["size"] or created.get("digest") not in (None, "sha256:" + item["sha256"]):
            raise ValueError("Uploaded asset validation failed")
        print("Verified:", item["name"], flush=True)
    fresh = api("/releases/" + str(release["id"]))
    remote = {item["name"]: item for item in fresh["assets"]}
    for item, _ in assets:
        if item["name"] not in remote or remote[item["name"]]["size"] != item["size"]:
            raise ValueError("Release is incomplete")
    if fresh["draft"]:
        fresh = api("/releases/" + str(release["id"]), {"draft": False, "make_latest": "true"}, "PATCH")
    print("Published:", fresh["html_url"])


if __name__ == "__main__":
    publish(Path(__file__).resolve().parents[2])
