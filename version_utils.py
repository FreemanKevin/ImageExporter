import re

def version_key(version):
    # 尝试将版本号转换为数字，如果失败则返回一个很小的值，确保这种版本号排在后面
    try:
        if version.startswith('v'):
            version = version[1:]
        elif re.match(r'^RELEASE\.\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z', version):
            return [-1]
        return [int(v) for v in re.split(r'[.-]', version)]
    except ValueError:
        return [-1]  # 返回一个非常小的值，确保这些版本号排在后面