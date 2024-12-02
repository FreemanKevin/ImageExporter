import os
import version_utils

def read_versions_from_file(filename):
    versions = {}
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            for line in file:
                if ':' in line:
                    component, version = line.strip().split(':')
                    versions[component] = version
    return versions

def find_previous_version_file():
    latest_files = [f for f in os.listdir('.') if f.startswith('latest-') and f.endswith('.txt')]
    if not latest_files:
        return None
    latest_files.sort(reverse=True)  # 按文件名排序，获取最新的文件
    return latest_files[1] if len(latest_files) > 1 else None

def write_versions_to_file(filename, versions):
    with open(filename, 'w') as file:
        for component, version in versions.items():
            file.write(f"{component}:{version}\n")

def compare_versions(current_versions, previous_versions):
    updates_needed = {}
    for component, current_version in current_versions.items():
        if component in previous_versions:
            if version_utils.version_key(current_version) > version_utils.version_key(previous_versions[component]):
                updates_needed[component] = current_version
    return updates_needed