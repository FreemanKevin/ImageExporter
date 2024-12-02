import requests
import time
import re
from config import DOCKER_HUB_API_URL,IK_PLUGIN_URL
from version_utils import version_key

def get_latest_versions(component, filter_func, max_retries=3, retry_delay=2):
    _, repo_path = component.split("docker.io/")
    all_tags = []
    page = 1
    while True:
        for attempt in range(max_retries):
            try:
                url = f"{DOCKER_HUB_API_URL}/repositories/{repo_path}/tags?page_size=100&page={page}"
                response = requests.get(url)
                response.raise_for_status()  # 如果请求失败，抛出异常
                tags = response.json()['results']

                # 过滤掉latest标签和不符合条件的标签
                tags = [tag for tag in tags if tag['name'] != 'latest' and filter_func(tag['name'])]
                all_tags.extend(tags)

                # 如果返回的结果少于page_size，说明这是最后一页
                if len(tags) < 100:
                    break

                page += 1
                break  # 如果成功获取一页数据，就跳出重试循环
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:  # 如果还有重试机会
                    print(f"Attempt {attempt + 1} failed for {component}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to retrieve versions for {component} after {max_retries} attempts. Error: {str(e)}")
                    break

        if len(tags) < 100:  # 如果最后一页的结果少于100，说明已经没有更多页了
            break

    if not all_tags:
        return [], f"No versions found after applying filter for {component}."

    # 根据版本号排序，取最新的1个
    all_tags.sort(key=lambda x: version_key(x['name']), reverse=True)
    latest_tags = [tag['name'] for tag in all_tags[:1]]
    return latest_tags, "Success"

def get_latest_ik_version():
    try:
        response = requests.get(IK_PLUGIN_URL)
        response.raise_for_status()
        content = response.text
        # 使用正则表达式提取版本号
        versions = re.findall(r'elasticsearch-analysis-ik-([\d.]+).zip', content)
        if versions:
            # 取最新的版本号
            latest_ik_version = max(versions, key=version_key)
            return latest_ik_version
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve IK plugin versions. Error: {str(e)}")
        return None