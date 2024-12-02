import os
import gzip
import shutil
import subprocess
from datetime import time
import file_utils

def pull_image(component, full_image_name, arch, max_retries=3, verbose=True):
    """尝试拉取指定架构的镜像"""
    for attempt in range(max_retries):
        try:
            subprocess.run(["docker", "pull", f"--platform=linux/{arch}", full_image_name], check=True, stdout=subprocess.DEVNULL if not verbose else None, stderr=subprocess.DEVNULL if not verbose else None)
            if verbose:
                print(f"[{arch}] 成功拉取镜像: {full_image_name}")
            break
        except subprocess.CalledProcessError:
            if attempt == max_retries - 1:
                if verbose:
                    print(f"[{arch}] 拉取 {full_image_name} 失败，共重试{max_retries}次。")
            else:
                if verbose:
                    print(f"[{arch}] 拉取 {full_image_name} 失败，尝试 {attempt + 1} 次...")
                time.sleep(2)

def export_image(full_image_name, image_path, arch, verbose=True):
    """导出镜像并直接压缩"""
    if verbose:
        print(f"[{arch}] 正在制作离线镜像文件: {image_path}")
    with subprocess.Popen(["docker", "save", full_image_name], stdout=subprocess.PIPE) as proc:
        with gzip.open(image_path, 'wb') as f:
            shutil.copyfileobj(proc.stdout, f)

def pull_and_export_images(updates_needed, current_date, verbose=True):
    """拉取并导出指定架构的镜像"""
    if not updates_needed:
        if verbose:
            print("\n无需拉取的任何镜像。")
        return

    update_file_name = f'update-{current_date}.txt'
    file_utils.write_versions_to_file(update_file_name, updates_needed)
    # 移除重复的打印语句
    # if verbose:
    #     print(f"\n需要拉取的新版镜像列表已保存至: {os.path.abspath(update_file_name)}")

    if os.path.getsize(update_file_name) > 0:
        offline_dir = f"{current_date}"
        os.makedirs(os.path.join(offline_dir, "AMD64"), exist_ok=True)
        os.makedirs(os.path.join(offline_dir, "ARM64"), exist_ok=True)

        for component, version in updates_needed.items():
            image_name = component.split('/')[-1]
            full_image_name = f"{component}:{version}"
            amd64_image_name = f"{image_name}_{version}_amd64_{current_date}.tar.gz"
            arm64_image_name = f"{image_name}_{version}_arm64_{current_date}.tar.gz"

            for arch, image_name in [("amd64", amd64_image_name), ("arm64", arm64_image_name)]:
                pull_image(component, full_image_name, arch, verbose=verbose)
                export_image(full_image_name, os.path.join(offline_dir, arch.upper(), image_name), arch, verbose=verbose)

        if verbose:
            print("\n所有镜像文件离线完成。")
            print(f"所在目录位置: {os.path.abspath(offline_dir)}")
    else:
        if verbose:
            print("没有需要拉取的镜像，跳过拉取任务。")
