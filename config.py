import re

# Docker Hub API base URL
DOCKER_HUB_API_URL = "https://hub.docker.com/v2"
IK_PLUGIN_URL = "https://release.infinilabs.com/analysis-ik/stable/"

# 需要查询的组件列表和对应的过滤函数
components = {
    "docker.io/library/elasticsearch": lambda x: x.startswith('8.'),
    "docker.io/minio/minio": lambda x: not x.endswith(('.fips', '-cpuv1')),
    "docker.io/nacos/nacos-server": lambda x: not x.endswith('-slim'),
    "docker.io/library/nginx": lambda x: re.match(r'^\d+\.\d+\.\d+$', x),
    "docker.io/library/rabbitmq": lambda x: x.endswith('-management-alpine') and not ('beta' in x or 'rc' in x),
    "docker.io/library/redis": lambda x: re.match(r'^\d+\.\d+\.\d+$', x),
    "docker.io/kartoza/geoserver": lambda x: re.match(r'^\d+\.\d+\.\d+$', x)
}