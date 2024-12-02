import os
import docker_utils
import file_utils

def pull_and_export_images(updates_needed, current_date, verbose=True):
    """拉取并导出指定架构的镜像"""
    if not updates_needed:
        if verbose:
            print("\n无需拉取的任何镜像。")
        return

    update_file_name = f'update-{current_date}.txt'
    file_utils.write_versions_to_file(update_file_name, updates_needed)

    if os.path.getsize(update_file_name) > 0:
        if verbose:
            print("\n>>>>>>>>>>>>>> 开始拉取镜像 <<<<<<<<<<<<<<")
        offline_dir = f"{current_date}"
        os.makedirs(os.path.join(offline_dir, "AMD64"), exist_ok=True)
        os.makedirs(os.path.join(offline_dir, "ARM64"), exist_ok=True)

        for component, version in updates_needed.items():
            image_name = component.split('/')[-1]
            full_image_name = f"{component}:{version}"
            amd64_image_name = f"{image_name}_{version}_amd64_{current_date}.tar.gz"
            arm64_image_name = f"{image_name}_{version}_arm64_{current_date}.tar.gz"

            for arch, image_name in [("amd64", amd64_image_name), ("arm64", arm64_image_name)]:
                docker_utils.pull_image(component, full_image_name, arch, verbose=verbose)
                docker_utils.export_image(full_image_name, os.path.join(offline_dir, arch.upper(), image_name), arch, verbose=verbose)

        if verbose:
            print("\n所有镜像文件离线完成。")
            print(f"所在目录位置: {os.path.abspath(offline_dir)}")
    else:
        if verbose:
            print("没有需要拉取的镜像，跳过拉取任务。")
