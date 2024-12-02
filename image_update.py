import os
from datetime import datetime
import file_utils

def compare_and_update(current_file_name, verbose=True):
    """比较版本并输出需要更新的镜像"""
    if verbose:
        print("\n>>>>>>>>>>>> 判断是否需要拉取镜像 <<<<<<<<<")
    previous_file = file_utils.find_previous_version_file()
    if previous_file:
        current_versions = file_utils.read_versions_from_file(current_file_name)
        previous_versions = file_utils.read_versions_from_file(previous_file)
        updates_needed = file_utils.compare_versions(current_versions, previous_versions)
        if updates_needed:
            update_file_name = f'update-{datetime.now().strftime('%Y%m%d')}.txt'
            file_utils.write_versions_to_file(update_file_name, updates_needed)
            if verbose:
                for component, version in updates_needed.items():
                    print(f"需要拉取的新版镜像: {component}:{version}")
                print(f"\n需要拉取的镜像列表已保存至: {os.path.abspath(update_file_name)}")
            return updates_needed
        else:
            if verbose:
                print("\n无需拉取的任何镜像。")
            return {}
    else:
        if verbose:
            print("\n没有找到上一个版本的文件，无法进行比较。")
        return {}
