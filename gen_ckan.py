import json
import os
import subprocess
import sys

from urllib.request import Request, urlopen

NETKAN = os.environ.get("NETKAN_PATH", r"C:\Users\Hayden\Downloads\netkan.exe")
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


def run_netkan(outputdir, netkan_path):
    os.makedirs(outputdir, exist_ok=True)
    cmd = [NETKAN, "--outputdir", outputdir, netkan_path]
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

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    repo_request = Request(
        url=f"https://api.github.com/repos/RSS-Reborn/Sol-{name}",
        headers=headers,
        method="GET",
    )
    repo_response = json.loads(urlopen(repo_request, timeout=5).read().decode('utf-8'))

    for variant in variants:
        netkan_path = f"netkan/sol-{name.lower()}/Sol-{name}-{variant}.netkan"
        conflicts = [f"Sol-{name}-{v}" for v in variants if v != variant]

        template = f"""identifier: Sol-{name}-{variant}
name: Sol {name} Textures ({variant})
abstract: {repo_response.get('description', f'The {variant} textures for Sol {name}.')}
license: restricted
author:
  - ballisticfox
  - Charon_S
$kref: '#/ckan/github/RSS-Reborn/Sol-{name}/asset_match/{zip_name}{variant}\\.(zip|7z)'
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
    ok = True

    for name, zip_name, variants in MODULES:
        if not generate_netkan(name, zip_name, variants):
            ok = False

    for outputdir, netkan_path in STANDALONE:
        if not run_netkan(outputdir, netkan_path):
            ok = False

    if not ok:
        sys.exit(1)

    print("All done.")


if __name__ == "__main__":
    main()
