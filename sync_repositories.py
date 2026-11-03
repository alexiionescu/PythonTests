import argparse
import fnmatch
import json
import os
import subprocess

DEFAULT_CONFIG_FILE = "config.json"


def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan root directories for standard and bare Git/Hg repositories up to 2 levels deep."
    )
    parser.add_argument(
        "config_file",
        nargs="?",
        default=DEFAULT_CONFIG_FILE,
        help=f"Path to the JSON configuration file (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Perform a dry run: scan and print intended actions without executing backups.",
    )
    return parser.parse_args()


def load_config(config_path):
    """Loads root configuration from the specified JSON file."""
    if not os.path.exists(config_path):
        if config_path == DEFAULT_CONFIG_FILE:
            sample_config = [
                {
                    "source_root": "D:\\MercurialRoot",
                    "backup_root": "E:\\MercurialRootBackup",
                    "exclude": ["Temp*", "OldRepository", "*_"],
                }
            ]
            with open(config_path, "w") as f:
                json.dump(sample_config, f, indent=4)
            print(
                f"Created a sample configuration file at '{config_path}'. Please edit it and run the script again."
            )
        else:
            print(f"Error: The configuration file '{config_path}' does not exist.")
        return []

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON configuration file '{config_path}': {e}")
        return []


def should_exclude(folder_name, exclude_patterns):
    """Checks if a folder name matches any of the given exclusion patterns."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(folder_name, pattern):
            return True
    return False


def check_vcs_type(path):
    """Returns 'git', 'hg', or None by checking standard and bare structures safely."""
    # 1. Check for standard Mercurial (.hg folder) or bare Mercurial (no native bare standard, checks folder)
    if os.path.exists(os.path.join(path, ".hg")):
        return "hg"

    # 2. Check for standard Git (.git folder)
    if os.path.exists(os.path.join(path, ".git")):
        return "git"

    # 3. Check if the directory itself is a Bare Git Repository.
    # Bare repos contain files like 'config', 'HEAD', and 'objects' right in the root.
    if os.path.exists(os.path.join(path, "HEAD")) and os.path.exists(
        os.path.join(path, "objects")
    ):
        # Double check using git command to be absolutely sure, feeding dynamic trust scope
        try:
            result = subprocess.run(
                ["git", "-c", "safe.directory=*", "rev-parse", "--is-bare-repository"],
                cwd=path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if "true" in result.stdout.strip().lower():
                return "git"
        except Exception:
            pass

    return None


def scan_repositories(source_root, backup_root, exclude_patterns):
    """Scans up to 2 levels deep for repositories, checking both standard and bare layouts."""
    discovered = []
    if not os.path.exists(source_root):
        print(f"Warning: Source root folder '{source_root}' does not exist. Skipping.")
        return discovered

    print(f"Scanning '{source_root}' up to 2 levels deep for repositories...")

    try:
        # --- LEVEL 1 SCAN ---
        for entry_l1 in os.scandir(source_root):
            if not entry_l1.is_dir():
                continue

            folder_name_l1 = entry_l1.name
            if should_exclude(folder_name_l1, exclude_patterns):
                print(f"Skipping excluded Level 1 folder: {folder_name_l1}")
                continue

            vcs_type_l1 = check_vcs_type(entry_l1.path)
            if vcs_type_l1:
                discovered.append(
                    {
                        "name": folder_name_l1,
                        "type": vcs_type_l1,
                        "remote": entry_l1.path,
                        "dest_path": os.path.join(backup_root, folder_name_l1),
                    }
                )

            # --- LEVEL 2 SCAN ---
            if folder_name_l1 in (".git", ".hg", "objects", "info", "hooks", "refs"):
                continue  # Ignore Git/Hg structural internals

            try:
                for entry_l2 in os.scandir(entry_l1.path):
                    if not entry_l2.is_dir():
                        continue

                    folder_name_l2 = entry_l2.name
                    if folder_name_l2 in (
                        ".git",
                        ".hg",
                        "objects",
                        "info",
                        "hooks",
                        "refs",
                    ):
                        continue

                    if should_exclude(folder_name_l2, exclude_patterns):
                        print(
                            f"Skipping excluded Level 2 folder: {folder_name_l1}/{folder_name_l2}"
                        )
                        continue

                    vcs_type_l2 = check_vcs_type(entry_l2.path)
                    if vcs_type_l2:
                        relative_dest_path = os.path.join(
                            folder_name_l1, folder_name_l2
                        )
                        discovered.append(
                            {
                                "name": f"{folder_name_l1}/{folder_name_l2}",
                                "type": vcs_type_l2,
                                "remote": entry_l2.path,
                                "dest_path": os.path.join(
                                    backup_root, relative_dest_path
                                ),
                            }
                        )
            except PermissionError:
                print(
                    f"Permission denied accessing subfolder level 2 of: {entry_l1.path}"
                )

    except PermissionError:
        print(f"Permission denied accessing source root: {source_root}")

    print(f"Found {len(discovered)} active repositories in '{source_root}'.")
    return discovered


def backup_git(path, remote, dry_run=False):
    is_new = not os.path.exists(path)
    if is_new:
        if dry_run:
            print(f"[DRY RUN] Would create new BARE Git backup at: {path}")
            print(
                f"          Command: git -c safe.directory=* clone --bare {remote} {path}"
            )
        else:
            print(f"Creating new BARE Git backup at {path}...")
            subprocess.run(
                ["git", "-c", "safe.directory=*", "clone", "--bare", remote, path],
                check=True,
            )
    else:
        if dry_run:
            print(f"[DRY RUN] Would fetch updates for bare Git repository at: {path}")
            print(
                f"          Command: git -c safe.directory=* -C {path} fetch origin *:* --prune"
            )
        else:
            print(f"Fetching latest updates for bare Git repository at {path}...")
            subprocess.run(
                [
                    "git",
                    "-c",
                    "safe.directory=*",
                    "-C",
                    path,
                    "fetch",
                    "origin",
                    "*:*",
                    "--prune",
                ],
                check=True,
            )


def backup_mercurial(path, remote, dry_run=False):
    is_new = not os.path.exists(path)
    if is_new:
        if dry_run:
            print(
                f"[DRY RUN] Would create new Mercurial backup (no working directory) at: {path}"
            )
            print(
                f"          Command: hg clone --noupdate --config extensions.largefiles= {remote} {path}"
            )
        else:
            print(f"Creating new Mercurial backup (no working directory) at {path}...")
            subprocess.run(
                [
                    "hg",
                    "clone",
                    "--noupdate",
                    "--config",
                    "extensions.largefiles=",
                    remote,
                    path,
                ],
                check=True,
            )
    else:
        if dry_run:
            print(f"[DRY RUN] Would pull updates for Mercurial repository at: {path}")
            print(
                f"          Command: hg pull -R {path} --config extensions.largefiles="
            )
        else:
            print(f"Pulling latest updates for Mercurial repository at {path}...")
            subprocess.run(
                ["hg", "pull", "-R", path, "--config", "extensions.largefiles="],
                check=True,
            )


def main():
    args = parse_arguments()
    config_entries = load_config(args.config_file)
    if not config_entries:
        return

    repositories_to_backup = []
    for entry in config_entries:
        if "source_root" in entry and "backup_root" in entry:
            exclude_patterns = entry.get("exclude", [])
            if not isinstance(exclude_patterns, list):
                exclude_patterns = [exclude_patterns]

            repos = scan_repositories(
                entry["source_root"], entry["backup_root"], exclude_patterns
            )
            repositories_to_backup.extend(repos)
        else:
            print(f"Skipping malformed entry in config: {entry}")

    if not repositories_to_backup:
        print("No repositories found to back up.")
        return

    if args.dry_run:
        print("\n" + "=" * 20 + " DRY RUN MODE ACTIVE " + "=" * 20)
        print("No changes will be written to the disk.\n")
    else:
        print("\nStarting backup process...\n" + "=" * 40)

    for repo in repositories_to_backup:
        path = repo["dest_path"]
        vcs_type = repo["type"]
        remote = repo["remote"]

        try:
            if vcs_type == "git":
                backup_git(path, remote, dry_run=args.dry_run)
            elif vcs_type == "hg":
                backup_mercurial(path, remote, dry_run=args.dry_run)

            if not args.dry_run:
                print(f"Successfully processed {repo['name']} ({vcs_type.upper()})\n")
            else:
                print()
        except subprocess.CalledProcessError as e:
            print(f"Error processing repository {repo['name']}: {e}\n")
        except Exception as e:
            print(f"Unexpected error with {repo['name']}: {e}\n")


if __name__ == "__main__":
    main()
