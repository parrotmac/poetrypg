import datetime
import os
import sys
import ruamel.yaml
from github import Github
from typing import List, Tuple
import subprocess
import requests


gh = Github(os.getenv("GITHUB_TOKEN"))
poetry_repo = gh.get_repo("python-poetry/poetry")
poetrypg_repo = gh.get_repo("parrotmac/poetrypg")
build_workflow_file = ".github/workflows/build.yaml"


def filter_releases(releases, count: int = 3, prerelease: bool = False) -> List[str]:
    return [
        release.tag_name for release in releases if release.prerelease == prerelease
    ][:count]


def update_workflow(
    fp,
    poetry_versions: List[str],
) -> Tuple[List[str], List[str]]:
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    data = yaml.load(fp)

    matrix = (
        data.get("jobs", {}).get("docker", {}).get("strategy", {}).get("matrix", {})
    )
    # TODO: Support fetching python versions from Docker hub
    matrix["python_version"] = ["3.9.12", "3.10.4"]
    matrix["debian_version"] = ["bullseye"]

    previous_poetry_versions = matrix.get("poetry_version", []).copy()

    # Identify which versions are new and which will be removed
    new_poetry_versions = [
        version
        for version in poetry_versions
        if version not in previous_poetry_versions
    ]
    removed_poetry_versions = [
        version
        for version in previous_poetry_versions
        if version not in poetry_versions
    ]

    if not new_poetry_versions and not removed_poetry_versions:
        print("No changes to Poetry versions")
        return

    matrix["poetry_version"] = poetry_versions

    fp.seek(0)
    fp.truncate()
    yaml.dump(data, fp)

    return new_poetry_versions, removed_poetry_versions


if __name__ == "__main__":

    branch_name = "bot-update-poetry-versions-1649738894"
    commit_summary = "Update Poetry versions"
    commit_description = f"{commit_summary}\n\n"


    releases = poetry_repo.get_releases()
    latest_stable = filter_releases(releases, count=1)
    latest_prerelease = filter_releases(releases, prerelease=True, count=1)
    poetry_versions = latest_stable + latest_prerelease

    with open(build_workflow_file, "r+") as fp:
        res = update_workflow(fp, poetry_versions)
        if not res:
            print(f"No new Poetry versions")
            sys.exit(0)

        new_poetry_versions, removed_poetry_versions = res

        if len(new_poetry_versions) != len(removed_poetry_versions):
            print(
                f"{len(new_poetry_versions)} new Poetry versions({new_poetry_versions}) and {len(removed_poetry_versions)} removed Poetry versions({removed_poetry_versions})"
            )
            sys.exit(1)
        
        if len(new_poetry_versions) == 0:
            print(f"No new Poetry versions")
            sys.exit(0)

        # Checkout new branch
        branch_name = f"bot_update-poetry-versions-{int(datetime.datetime.now().timestamp())}"
        subprocess.check_call(["git", "checkout", "-b", branch_name])
        
        commit_summary = "Bump Poetry versions to {}".format(", ".join(new_poetry_versions))
        commit_description = ""

        if len(new_poetry_versions) > 1:
          for i, _ in enumerate(new_poetry_versions):
            commit_description += f"* {removed_poetry_versions[i]} -> {new_poetry_versions[i]}\n"
        
        # I did not have luck using GitPython to do this :(
        subprocess.check_call(["git", "add", build_workflow_file])
        subprocess.check_call(["git", "commit", "-m", commit_summary, "-m", commit_description])
        subprocess.check_call(["git", "push", "origin", branch_name])

        pr = poetrypg_repo.create_pull(title=f"[bot] {commit_summary}", body=f"{commit_summary}\n{commit_description}", head=branch_name, base="main")
        print(f"Created PR: {pr.html_url}")
        exit(0)