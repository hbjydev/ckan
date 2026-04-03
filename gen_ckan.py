import argparse
import json
import os
import subprocess
import sys

from urllib.request import Request, urlopen

NETKAN_PATH = os.environ.get("NETKAN_PATH", r"C:\Users\Hayden\Downloads\netkan.exe")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

MODULES = [
    ("Launchsites", "Launchsites-", ["256x", "512x", "1024x"]),
    ("Sun", "Sol_Sol_", ["4k", "8k", "16k"]),
    ("Mercury", "Sol_Mercury_", ["4k", "8k", "16k"]),
    ("Venus", "Sol_Venus_", ["4k", "8k", "16k"]),
    ("EarthSystem", "Sol_Earth-System_", ["4k", "8k", "16k"]),
    ("MarsSystem", "Sol_Mars-System_", ["4k", "8k", "16k"]),
    ("JupiterSystem", "Sol_Jupiter-System_", ["4k", "8k", "16k"]),
    ("SaturnSystem", "Sol_Saturn-System_", ["4k", "8k", "16k"]),
    ("UranusSystem", "Sol_Uranus-System_", ["4k", "8k", "16k"]),
    ("NeptuneSystem", "Sol_Neptune-System_", ["4k", "8k", "16k"]),
    ("AsteroidBelt", "Sol_Asteroid-Belt_", ["4k", "8k", "16k"]),
    ("KuiperBelt", "Sol_Kuiper-Belt_", ["4k", "8k", "16k"]),
]

STANDALONE = [
    ("ckan/ParallaxContinued-KTL", "netkan/ParallaxContinued-KTL.netkan"),
    ("ckan/Sol-Configs", "netkan/Sol-Configs.netkan"),
    ("ckan/Sol-Core", "netkan/Sol-Core.netkan"),
    ("ckan/Sol-Visuals", "netkan/Sol-Visuals.netkan"),
]


def github_api_request(url):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    request = Request(url=url, headers=headers, method="GET")
    response = urlopen(request, timeout=5)
    return json.loads(response.read().decode('utf-8'))


def run_netkan(outputdir, netkan_path):
    os.makedirs(outputdir, exist_ok=True)
    cmd = [NETKAN_PATH, "--outputdir", outputdir, netkan_path]
    if GITHUB_TOKEN:
        cmd[1:1] = ["--github-token", GITHUB_TOKEN]
    print(f"  Running netkan: {netkan_path} -> {outputdir}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  ERROR: netkan failed for {netkan_path}", file=sys.stderr)
        return False
    return True


def generate_netkan(name, zip_name, variants):
    ok = True
    repo_data = github_api_request(f"https://api.github.com/repos/RSS-Reborn/Sol-{name}")

    for variant in variants:
        netkan_path = f"netkan/sol-{name.lower()}/Sol-{name}-{variant}.netkan"
        conflicts = [f"Sol-{name}-{v}" for v in variants if v != variant]

        template = f"""identifier: Sol-{name}-{variant}
name: Sol {name} Textures ({variant})
abstract: {repo_data.get('description', f'The {variant} textures for Sol {name}.')}
license: restricted
author:
  - ballisticfox
  - Charon_S
$kref: '#/ckan/github/RSS-Reborn/Sol-{name}/asset_match/{zip_name}{variant}(\\-[0-9]+)?\\.zip'
release_status: stable
resources:
  bugtracker: https://github.com/RSS-Reborn/Sol-{name}/issues
  manual: https://github.com/RSS-Reborn/Sol-Configs/wiki
  homepage: https://github.com/RSS-Reborn/Sol-Configs/wiki
  repository: https://github.com/RSS-Reborn/Sol-{name}
tags:
  - config
  - planet-pack
ksp_version_min: '1.12'
install:
  - file: GameData/Sol-Textures
    install_to: GameData
provides:
  - Sol-{name}
depends:
  - name: Sol-Core"""

        if conflicts:
            template += "\nconflicts:\n  - name: " + "\n  - name: ".join(conflicts)

        os.makedirs(os.path.dirname(netkan_path), exist_ok=True)
        with open(netkan_path, "w") as f:
            f.write(template)

        print(f"Generated {netkan_path}")

        if not run_netkan(f"ckan/Sol-{name}", netkan_path):
            ok = False

    return ok


def main():
    parser = argparse.ArgumentParser(description="Generate CKAN files")
    parser.add_argument("names", nargs="*", help="Names of specific modules/standalone entries to update (e.g. EarthSystem Sol-Core)")
    parser.add_argument("-n", "--netkan-path", default=NETKAN_PATH, help="Path to netkan.exe (default: %(default)s)")
    parser.add_argument("-g", "--github-token", default=GITHUB_TOKEN, help="GitHub token for API access (default: %(default)s)")
    args = parser.parse_args()

    filter_names = set(args.names)
    ok = True

    for name, zip_name, variants in MODULES:
        if filter_names and name not in filter_names:
            continue
        if not generate_netkan(name, zip_name, variants):
            ok = False

    for outputdir, netkan_path in STANDALONE:
        entry_name = os.path.splitext(os.path.basename(netkan_path))[0]
        if filter_names and entry_name not in filter_names:
            continue
        if not run_netkan(outputdir, netkan_path):
            ok = False

    if not ok:
        sys.exit(1)

    print("All done.")


if __name__ == "__main__":
    main()
