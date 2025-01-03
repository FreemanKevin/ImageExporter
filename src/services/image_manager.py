import os
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from src.utils.docker_utils import (
    logger,
    get_version_file_path,
    get_output_path,
    write_versions_to_file,
    VERSIONS_DIR,
    OUTPUT_DIR,
    pull_image,
    export_image
)
from src.config import CONFIG

console = Console()

class ImageManager:
    def __init__(self):
        self.state_file = "state.json"
        self.today = datetime.now().strftime('%Y%m%d')
        self.state = self.load_state()

    def load_state(self):
        """从状态文件中加载上次执行的状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("状态文件损坏，将重新开始任务")
                return None
        return None

    def save_state(self, last_step, updates_needed):
        """保存当前状态到状态文件"""
        state = {
            "current_date": self.today,
            "last_step": last_step,
            "updates_needed": updates_needed
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    def clean_state(self):
        """清理状态文件"""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def compare_and_update(self, components):
        """比较版本并输出需要更新的镜像"""
        try:
            console.print("\n[bold cyan]════════ 开始执行更新检查 ════════[/bold cyan]\n")
            
            # 获取历史版本文件
            history_versions = self._get_latest_history_file()
            if not history_versions:
                console.print("\n[bold yellow]未找到历史版本文件，将视为全新安装[/bold yellow]\n")
            
            # 使用进度动画获取最新版本
            with Progress(
                SpinnerColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("", total=None)
                
                # 获取最新版本
                for name, component in components.items():
                    latest_version = CONFIG.get_latest_version(name)
                    component['latest_version'] = latest_version
                
                progress.update(task, description="")
            
            # 保存最新版本列表
            self._save_latest_versions(components)
            
            # 检查需要更新的组件
            updates_needed = self._check_updates(components, history_versions) if history_versions else components
            
            return updates_needed
            
        except Exception as e:
            console.print(f"\n[bold red]检查更新时出错: {str(e)}[/bold red]\n")
            raise

    def pull_and_export_images(self, updates_needed):
        """拉取并导出需要更新的镜像"""
        try:
            with Progress(
                SpinnerColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                overall_task = progress.add_task(
                    "", 
                    total=len(updates_needed) * 2
                )
                console.print()  # 添加换行
                
                with ThreadPoolExecutor(max_workers=CONFIG.get("concurrent_downloads", 2)) as executor:
                    futures = []
                    for name, component in updates_needed.items():
                        image_name = component['image']
                        version = component['latest_version']
                        if not version:
                            continue
                            
                        full_image_name = f"{image_name}:{version}"
                        
                        for arch in ['amd64', 'arm64']:
                            image_path = os.path.join(
                                get_output_path(self.today, arch),
                                f"{os.path.basename(image_name)}:{version}.tar.gz"
                            )
                            
                            futures.append(
                                executor.submit(
                                    self._process_image,
                                    full_image_name,
                                    image_path,
                                    arch,
                                    progress,
                                    overall_task
                                )
                            )
                    
                    # 等待所有任务完成
                    for future in futures:
                        future.result()
                        
                console.print()  # 添加换行
                    
        except Exception as e:
            console.print(f"\n[bold red]拉取和导出镜像时出错: {str(e)}[/bold red]\n")
            raise

    def _process_image(self, full_image_name, image_path, arch, progress, overall_task):
        """处理单个镜像的拉取和导出"""
        try:
            # 拉取镜像
            progress.update(overall_task, description="")
            console.print()  # 添加换行
            
            if pull_image(None, full_image_name, arch):
                progress.advance(overall_task, 0.5)
                console.print()  # 添加换行
            
            # 导出镜像
            progress.update(overall_task, description="")
            console.print()  # 添加换行
            
            export_image(full_image_name, image_path, arch)
            progress.advance(overall_task, 0.5)
            console.print()  # 添加换行
            
        except Exception as e:
            console.print(f"\n[bold red][{arch}] 处理镜像失败:[/bold red] {full_image_name}, {str(e)}\n")
            raise

    def _get_latest_history_file(self):
        """获取最新的历史版本文件"""
        try:
            if not os.path.exists(VERSIONS_DIR):
                return None
                
            history_files = []
            for file in os.listdir(VERSIONS_DIR):
                if file.startswith("latest-") and file.endswith(".txt"):
                    date_str = file.split("-")[1].split(".")[0]
                    if date_str != self.today:  # 排除今天的文件
                        history_files.append((date_str, os.path.join(VERSIONS_DIR, file)))
                        
            if not history_files:
                return None
                
            history_files.sort(reverse=True)
            return history_files[0][1]
            
        except Exception as e:
            logger.error(f"查找历史版本文件时出错: {str(e)}")
            return None

    def _check_updates(self, components, history_versions):
        """检查需要更新的组件"""
        old_versions = self._load_history_versions(history_versions)
        
        # 显示使用的版本文件
        if history_versions:
            console.print(f"\n[bold cyan]使用历史版本文件:[/bold cyan] {os.path.basename(history_versions)}\n")
        
        # 创建表格，设置标题为粗体但不倾斜
        table = Table(
            title="[bold]版本更新检查结果[/bold]",
            title_style="bold",
            title_justify="center",
            show_header=True,
            header_style="bold"
        )
        table.add_column("组件", style="bold")
        table.add_column("当前版本", style="bold")
        table.add_column("最新版本", style="bold")
        table.add_column("状态", style="bold")
        
        updates_needed = {}
        for name, component in components.items():
            # 修复 nacos 版本获取，使用完整的镜像名称
            image_name = os.path.basename(component['image'])
            old_version = old_versions.get(image_name)
            latest_version = component.get('latest_version')
            
            if latest_version:
                status = "[bold green]无需更新[/bold green]" if old_version == latest_version else "[bold red]需要更新[/bold red]"
                table.add_row(
                    f"[bold]{component['name']}[/bold]",
                    f"[bold yellow]{old_version or '无'}[/bold yellow]",
                    f"[bold green]{latest_version}[/bold green]",
                    status
                )
                
                if not old_version or latest_version != old_version:
                    updates_needed[name] = component
        
        console.print(table)
        
        # 显示最新版本文件
        latest_file = f"latest-{self.today}.txt"
        console.print(f"\n[bold cyan]新的版本信息将保存至:[/bold cyan] {latest_file}\n")
        
        return updates_needed

    def _load_history_versions(self, history_file):
        """加载历史版本信息"""
        old_versions = {}
        try:
            with open(history_file, 'r') as f:
                for line in f:
                    if line.strip():
                        image_path = line.strip()
                        # 使用完整的镜像名称作为键
                        image_name = os.path.basename(image_path.split(':')[0])
                        version = image_path.split(':')[1]
                        old_versions[image_name] = version
            return old_versions
        except Exception as e:
            logger.error(f"读取历史版本文件失败: {str(e)}")
            return {}

    def _save_latest_versions(self, components):
        """保存最新版本列表"""
        latest_file = get_version_file_path(f"latest-{self.today}.txt")
        with open(latest_file, 'w') as f:
            for name, component in components.items():
                if component.get('latest_version'):
                    f.write(f"{component['image']}:{component['latest_version']}\n")

    def run(self):
        """执行主要业务逻辑"""
        # 获取组件配置
        components = CONFIG.get("components")
        if not components:
            console.print("[bold red]未找到组件配置[/bold red]")
            return

        # 比较版本并获取需要更新的组件
        updates_needed = self.compare_and_update(components)
        
        # 如果有需要更新的组件，执行拉取和导出操作
        if updates_needed:
            console.print("\n[bold cyan]════════ 开始处理需要更新的镜像 ════════[/bold cyan]")
            self.pull_and_export_images(updates_needed)
            console.print("\n[bold green]所有更新任务已完成[/bold green]")
        else:
            console.print("\n[bold green]没有需要更新的组件[/bold green]")