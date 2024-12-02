import api
import config
import version_utils

def get_latest_ik_plugin(verbose=True, print_title=True):
    """获取IK插件的最新版本并打印结果"""
    if verbose and print_title:
        print("\n>>>>>>>>>>>> 获取最新Ik插件版本 <<<<<<<<<<<<")
    latest_ik_version = api.get_latest_ik_version()
    if latest_ik_version:
        if verbose:
            print(latest_ik_version)
    else:
        if verbose:
            print("无法获取IK插件版本")
    return latest_ik_version

def fetch_latest_images(verbose=True, print_title=True):
    """获取最新的镜像列表"""
    if verbose and print_title:
        print("\n>>>>>>>>>>>> 获取最新镜像列表 <<<<<<<<<<<<")
    versions = {}
    latest_ik_version = api.get_latest_ik_version()
    for component, filter_func in config.components.items():
        latest_versions, status = api.get_latest_versions(component, filter_func)
        if component == "docker.io/library/elasticsearch":
            versions[component] = handle_elasticsearch_version(latest_versions, latest_ik_version)
        else:
            versions[component] = latest_versions[0] if latest_versions else status
        if verbose and latest_versions:
            print(f"{component}:{latest_versions[0]}")
        elif verbose:
            print(f"{component}: {status}")
    return versions

def handle_elasticsearch_version(latest_versions, latest_ik_version):
    """处理Elasticsearch版本与IK插件版本的关系"""
    if latest_versions:
        latest_elasticsearch_version = latest_versions[0]
        if latest_ik_version and version_utils.version_key(latest_ik_version) < version_utils.version_key(latest_elasticsearch_version):
            return latest_ik_version
        return latest_elasticsearch_version
    return "No versions found"
