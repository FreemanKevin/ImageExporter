import os
import json
from datetime import datetime
import image_fetch
import image_update
import image_pull
import file_utils

def load_state():
    """从状态文件中加载上次执行的状态"""
    if os.path.exists("state.json"):
        with open("state.json", "r") as f:
            return json.load(f)
    return None

def save_state(current_date, last_step, updates_needed):
    """保存当前状态到状态文件"""
    state = {
        "current_date": current_date,
        "last_step": last_step,
        "updates_needed": updates_needed
    }
    with open("state.json", "w") as f:
        json.dump(state, f)

def check_and_pull_updates(verbose=True):
    """检查版本更新并拉取镜像"""
    state = load_state()
    if state:
        current_date = state["current_date"]
        updates_needed = state["updates_needed"]
        last_step = state["last_step"]
    else:
        current_date = datetime.now().strftime('%Y%m%d')
        latest_ik_version = image_fetch.get_latest_ik_plugin(verbose, print_title=True)  # 提前获取IK插件版本
        latest_versions = image_fetch.fetch_latest_images(verbose, print_title=True)  # 打印获取最新镜像列表的标题
        current_file_name = f'latest-{current_date}.txt'
        file_utils.write_versions_to_file(current_file_name, latest_versions)
        if verbose:
            print(f"最新镜像文件已保存至: {os.path.abspath(current_file_name)}")
        updates_needed = image_update.compare_and_update(current_file_name, verbose)
        last_step = "fetch_latest_images"
        # 保存获取镜像列表后的状态
        save_state(current_date, last_step, updates_needed)

    if last_step == "fetch_latest_images":
        if updates_needed:
            try:
                image_pull.pull_and_export_images(updates_needed, current_date, verbose)
            except Exception as e:
                # 如果在拉取过程中出现异常，保存当前状态并退出
                print(f"在拉取过程中出现异常: {e}")
                save_state(current_date, last_step, updates_needed)
                return
        last_step = "pull_and_export_images"

    # 保存完成所有任务后的状态
    save_state(current_date, last_step, updates_needed)

    # 清理状态文件 (仅在完成所有任务后)
    if last_step == "pull_and_export_images":
        if os.path.exists("state.json"):
            os.remove("state.json")
