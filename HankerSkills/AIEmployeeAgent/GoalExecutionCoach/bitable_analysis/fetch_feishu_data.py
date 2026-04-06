#!/usr/bin/env python3
"""
从飞书多维表格获取时间数据的脚本（支持两种授权方式）
基于 read_bitable.py 复用

本文件为 bitable_analysis/ 目录内的独立副本，配置从同目录下的 .env 读取。

特点：
- 仅执行读取操作，不修改任何数据
- 支持 COZE 方式（原有的 Skill 授权）
- 支持飞书开放平台 OAuth 2.0（app_id + app_secret）

数据源：https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h
"""

import sys
import os
from datetime import datetime, timedelta

# 加载 .env 文件（如果存在）
def load_env_file():
    """从 bitable_analysis/.env 加载环境变量（与本文件同目录）"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        return None

# 加载 .env 文件
load_env_file()

# 导入 coze_workload_identity 中的 requests
try:
    from coze_workload_identity import requests
except ImportError:
    import requests

# 飞书配置（从环境变量读取）
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN", "AUagbEJ3ZadyjwsfjAPcD991nGg")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tblFXOx2aYXcDLLw")
FEISHU_VIEW_ID = os.getenv("FEISHU_VIEW_ID", "vewjPhzV7h")

# OAuth 凭证配置
# 支持两种授权方式：
# 方式一：COZE 方式（原有的 Skill 凭证）
# 方式二：飞书开放平台 OAuth 2.0（app_id + app_secret）
SKILL_ID = "7605639493156274228"


def determine_token_type():
    """
    判断使用哪种 token 类型
    """
    # 优先使用飞书开放平台 OAuth 2.0
    oauth_token = os.getenv("FEISHU_OAUTH_ACCESS_TOKEN", "")

    if oauth_token:
        print(f"[INFO] 使用飞书开放平台 OAuth 2.0 方式（已有 token）", file=sys.stderr)
        return "oauth_open"  # 飞书开放平台 OAuth 2.0（已有 token）

    # 检查是否有 app_id 和 app_secret，可以获取新 token
    app_id = os.getenv("FEISHU_APP_ID", "")
    app_secret = os.getenv("FEISHU_APP_SECRET", "")

    if app_id and app_secret:
        print(f"[INFO] 使用飞书开放平台 OAuth 2.0 方式（使用 app_id/app_secret 获取 token）", file=sys.stderr)
        return "oauth_open_auto"  # 飞书开放平台 OAuth 2.0（自动获取 token）

    # 检查是否为 COZE 方式
    coze_token = os.getenv(f"COZE_FEISHU_BITABLE_{SKILL_ID}", "")
    if coze_token:
        print(f"[INFO] 使用 COZE 方式", file=sys.stderr)
        return "coze"  # COZE 方式

    else:
        return None  # 未知类型


def get_access_token():
    """
    获取飞书 OAuth 访问令牌（自动选择正确类型）
    """
    token_type = determine_token_type()

    if token_type == "oauth_open":
        # 飞书开放平台 OAuth 2.0：使用 FEISHU_OAUTH_ACCESS_TOKEN
        oauth_token = os.getenv("FEISHU_OAUTH_ACCESS_TOKEN", "")

        if not oauth_token:
            raise ValueError(
                "缺少飞书开放平台 OAuth 2.0 凭证。\n"
                "请设置环境变量 FEISHU_OAUTH_ACCESS_TOKEN\n"
            )

        return oauth_token

    elif token_type == "oauth_open_auto":
        # 飞书开放平台 OAuth 2.0：使用 app_id + app_secret 自动获取 token
        app_id = os.getenv("FEISHU_APP_ID", "")
        app_secret = os.getenv("FEISHU_APP_SECRET", "")

        if not app_id or not app_secret:
            raise ValueError(
                "缺少飞书开放平台凭证。\n"
                "请设置环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET\n"
            )

        # 调用飞书 API 获取 tenant_access_token
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": app_id,
            "app_secret": app_secret
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(token_url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                raise Exception(f"获取 access_token 失败: HTTP {response.status_code}")

            data = response.json()

            if data.get("code") != 0:
                error_msg = data.get("msg", "未知错误")
                raise Exception(f"获取 access_token 失败: {error_msg}")

            access_token = data.get("tenant_access_token", "")

            if not access_token:
                raise Exception("获取 access_token 失败: 响应中无 token")

            return access_token

        except requests.exceptions.RequestException as e:
            raise Exception(f"API 调用失败: {str(e)}")

    elif token_type == "coze":
        # COZE 方式：使用 COZE_FEISHU_BITABLE_{SKILL_ID}
        coze_token = os.getenv(f"COZE_FEISHU_BITABLE_{SKILL_ID}", "")

        if not coze_token:
            raise ValueError(
                f"缺少 COZE OAuth 凭证（Skill 授权）。\n"
                "请设置环境变量 COZE_FEISHU_BITABLE_{SKILL_ID}，或设置 FEISHU_OAUTH_ACCESS_TOKEN 切换到飞书开放平台方式\n"
            )

        return coze_token

    else:
        raise ValueError("未知的 token 类型配置，请检查环境变量")


def get_auth_headers():
    """
    根据使用的 token 类型返回正确的认证 headers
    """
    token_type = determine_token_type()

    if token_type == "oauth_open" or token_type == "oauth_open_auto":
        # 飞书开放平台 OAuth 2.0
        # 注意：oauth_open 使用 FEISHU_OAUTH_ACCESS_TOKEN
        #       oauth_open_auto 使用 app_id/app_secret 获取的 token
        # 两种方式都使用相同的 header 格式
        access_token = get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    elif token_type == "coze":
        # COZE 方式：使用 COZE_FEISHU_BITABLE_{SKILL_ID}
        coze_token = os.getenv(f"COZE_FEISHU_BITABLE_{SKILL_ID}", "")

        headers = {
            "Authorization": f"Bearer {coze_token}",
            "Content-Type": "application/json"
        }
    else:
        raise ValueError("未知的 token 类型")

    return headers


def fetch_feishu_records(period_start=None, period_end=None):
    """
    从飞书多维表格获取记录

    支持两种授权方式：
    - OAuth 2.0：使用 app_id + app_secret
    - COZE：使用 Skill 的 access_token

    支持日期筛选：
    - period_start: datetime 对象，筛选开始日期
    - period_end: datetime 对象，筛选结束日期

    根据使用的方式不同，API URL 和认证方式也会不同
    """
    access_token = get_access_token()
    headers = get_auth_headers()

    # 确定 API URL 和认证方式
    token_type = determine_token_type()

    if token_type == "oauth_open" or token_type == "oauth_open_auto":
        # 飞书开放平台 OAuth 2.0：使用 bitable API
        # API 文档参考：https://open.feishu.cn/document/ukTMukTMukTM/uYjNwUjL2YDM14iN2ATN
        api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"

    elif token_type == "coze":
        # COZE 方式：使用 Skill 的 access_token
        # 与现有 read_bitable.py 相同
        api_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_APP_TOKEN}/tables/{FEISHU_TABLE_ID}/records"

    else:
        raise ValueError("未知的授权方式")

    # 分页获取所有记录
    all_records = []
    page_token = ""

    # 转换日期格式用于筛选
    start_date_str = None
    end_date_str = None

    if period_start and period_end:
        start_date_str = period_start.strftime("%Y-%m-%d")
        end_date_str = period_end.strftime("%Y-%m-%d")

    try:
        while True:
            params = {
                "page_size": 500
            }

            if FEISHU_VIEW_ID:
                params["view_id"] = FEISHU_VIEW_ID

            if page_token:
                params["page_token"] = page_token

            # 发起 GET 请求（只读操作）
            response = requests.get(
                api_url,
                headers=headers,
                params=params,
                timeout=30
            )

            # 检查 HTTP 状态码
            if response.status_code >= 400:
                raise Exception(f"HTTP 请求失败: 状态码 {response.status_code}, 响应内容: {response.text}")

            data = response.json()

            # 错误处理
            code = data.get("code", 0)
            if code != 0:
                msg = data.get("msg", "未知错误")
                raise Exception(f"飞书接口错误[{code}]: {msg}")

            # 提取记录
            records = data.get("data", {}).get("items", [])

            # 如果指定了日期范围，进行筛选
            if period_start and period_end:
                filtered_records = []
                for record in records:
                    fields = record.get('fields', {})
                    # 获取开始时间（毫秒时间戳）
                    start_time = fields.get('开始时间', 0)
                    if start_time:
                        # 转换为 datetime 对象
                        from datetime import datetime as dt
                        record_date = dt.fromtimestamp(start_time / 1000)
                        # 检查是否在指定范围内
                        if period_start <= record_date <= period_end:
                            filtered_records.append(record)
                all_records.extend(filtered_records)
            else:
                all_records.extend(records)

            # 检查是否还有更多数据
            has_more = data.get("data", {}).get("has_more", False)
            if not has_more:
                break

            page_token = data.get("data", {}).get("page_token", "")

    except requests.exceptions.RequestException as e:
        raise Exception(f"API 调用失败: {str(e)}")

    return all_records


# 时间类别映射（根据飞书表格实际字段更新）
# 数据结构说明：
# - 一级分类 (primary_category): "👩‍💻 工作", "🎮 娱乐", "🧑‍🍳 生活" 等
# - 二级分类 (secondary_category): "💼 其他工作", "👑 创作", "💆 放松", "📀 刷视频" 等
CATEGORY_MAPPINGS = {
    'work': {
        'type': 'primary',  # 基于一级分类统计
        'values': ['👩‍💻 工作']
    },
    'creation': {
        'type': 'both',  # 基于一级和二级分类联合统计
        'primary': '👩‍💻 工作',
        'secondary': ['👑 创作']
    },
    'entertainment': {
        'type': 'secondary',  # 基于二级分类统计
        'values': ['💆 放松', '📀 刷视频', '📱 刷社交媒体', '🪁 其他娱乐']
    },
    'exercise': {
        'type': 'primary',  # 基于一级分类统计
        'values': ['🏋️ 运动']
    },
}


def calculate_category_duration(records, category_config):
    """
    计算指定类别的总时长（小时）

    Args:
        records: 飞书记录列表
        category_config: CATEGORY_MAPPINGS 中的值（配置对象）或键（字符串）

    Returns:
        float: 总时长（小时）
    """
    # 如果传入的是字符串键，获取对应的配置
    if isinstance(category_config, str):
        category_config = CATEGORY_MAPPINGS.get(category_config, {})

    total_hours = 0.0

    for record in records:
        fields = record.get('fields', {})

        # 获取一级分类字段
        primary_category = fields.get('一级分类', '')
        # 处理一级分类字段（可能是列表）
        if isinstance(primary_category, list) and len(primary_category) > 0:
            if isinstance(primary_category[0], dict):
                primary_category = primary_category[0].get('text', '')
            else:
                primary_category = str(primary_category[0])

        # 获取二级分类字段
        secondary_category = fields.get('二级分类', '')
        # 处理二级分类字段（可能是列表）
        if isinstance(secondary_category, list) and len(secondary_category) > 0:
            if isinstance(secondary_category[0], dict):
                secondary_category = secondary_category[0].get('text', '')
            else:
                secondary_category = str(secondary_category[0])

        # 获取时长字段（根据飞书表格实际字段名）
        duration = fields.get('任务时长（小时）', 0) or fields.get('时长', 0) or fields.get('Duration', 0) or fields.get('小时', 0)

        # 转换为浮点数
        try:
            duration = float(duration)
        except (ValueError, TypeError):
            continue

        # 根据类别配置的类型进行匹配
        match = False
        if category_config.get('type') == 'primary':
            # 只匹配一级分类
            if primary_category in category_config.get('values', []):
                match = True
        elif category_config.get('type') == 'secondary':
            # 只匹配二级分类
            if secondary_category in category_config.get('values', []):
                match = True
        elif category_config.get('type') == 'both':
            # 同时匹配一级和二级分类
            if (primary_category == category_config.get('primary') and
                secondary_category in category_config.get('secondary', [])):
                match = True

        if match:
            total_hours += duration

    return total_hours


def calculate_daily_work_time(period_start, period_end):
    """计算每日工作时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['work'])


def calculate_weekly_work_time(period_start, period_end):
    """计算每周工作时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['work'])


def calculate_daily_creation_time(period_start, period_end):
    """计算每日创作时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['creation'])


def calculate_weekly_creation_time(period_start, period_end):
    """计算每周创作时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['creation'])


def calculate_daily_entertainment_time(period_start, period_end):
    """计算每日娱乐+放松时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['entertainment'])


def calculate_daily_exercise_time(period_start, period_end):
    """计算每日运动时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['exercise'])


def calculate_weekly_exercise_time(period_start, period_end):
    """计算每周运动时间（小时）"""
    records = fetch_feishu_records(period_start, period_end)
    return calculate_category_duration(records, CATEGORY_MAPPINGS['exercise'])


def calculate_current_value_real(period_start, period_end, metric_type=None):
    """
    主计算函数（真实数据版本）

    Args:
        period_start: datetime 对象，周期开始时间
        period_end: datetime 对象，周期结束时间
        metric_type: str，可选指标类型，支持以下值：
            - 'daily_work_time': 每日工作时间
            - 'weekly_work_time': 每周工作时间
            - 'daily_creation_time': 每日创作时间
            - 'weekly_creation_time': 每周创作时间
            - 'daily_entertainment_time': 每日娱乐+放松时间
            - 'daily_exercise_time': 每日运动时间
            - 'weekly_exercise_time': 每周运动时间
            如果为 None，返回所有值中第一个非零的值（向后兼容）

    Returns:
        float: 计算得到的当前值
    """
    records = fetch_feishu_records(period_start, period_end)

    # 计算所有可能的指标
    values = {
        'daily_work_time': calculate_category_duration(records, CATEGORY_MAPPINGS['work']),
        'weekly_work_time': calculate_category_duration(records, CATEGORY_MAPPINGS['work']),
        'daily_creation_time': calculate_category_duration(records, CATEGORY_MAPPINGS['creation']),
        'weekly_creation_time': calculate_category_duration(records, CATEGORY_MAPPINGS['creation']),
        'daily_entertainment_time': calculate_category_duration(records, CATEGORY_MAPPINGS['entertainment']),
        'daily_exercise_time': calculate_category_duration(records, CATEGORY_MAPPINGS['exercise']),
        'weekly_exercise_time': calculate_category_duration(records, CATEGORY_MAPPINGS['exercise']),
    }

    # 如果指定了 metric_type，返回对应的值
    if metric_type and metric_type in values:
        return values[metric_type]

    # 临时方案：返回所有值中第一个非零的值（向后兼容）
    for value in values.values():
        if value > 0:
            return value

    return 0.0


def calculate_current_value_mock(period_start, period_end):
    """
    模拟版本的当前值计算（用于测试）
    """
    # 内联 CATEGORY_MAPPINGS
    category_mappings = {
        'work': ['工作'],
        'creation': ['创作'],
        'entertainment': ['娱乐', '生活-放松'],
        'exercise': ['运动'],
    }

    # 使用模拟数据
    mock_records = [
        {
            'fields': {
                '日期': '2026-02-26',
                '类别': '工作',
                '时长': 6.5
            }
        },
        {
            'fields': {
                '日期': '2026-02-26',
                '类别': '创作',
                '时长': 4.2
            }
        },
        {
            'fields': {
                '日期': '2026-02-26',
                '类别': '娱乐',
                '时长': 0.8
            }
        },
        {
            'fields': {
                '日期': '2026-02-26',
                '类别': '运动',
                '时长': 0.6
            }
        },
    ]

    # 对于 weekly，模拟多天数据
    if (period_end - period_start).days > 1:
        for day in range(1, min(7, (period_end - period_start).days)):
            current_date = (period_start + timedelta(days=day)).strftime("%Y-%m-%d")
            mock_records.append({
                'fields': {
                    '日期': current_date,
                    '类别': '工作',
                    '时长': 5.0
                }
            })

    # 计算所有类别的时长
    values = {
        'work': sum(r['fields']['时长'] for r in mock_records if r['fields']['类别'] in category_mappings['work']),
        'creation': sum(r['fields']['时长'] for r in mock_records if r['fields']['类别'] in category_mappings['creation']),
        'entertainment': sum(r['fields']['时长'] for r in mock_records if r['fields']['类别'] in category_mappings['entertainment']),
        'exercise': sum(r['fields']['时长'] for r in mock_records if r['fields']['类别'] in category_mappings['exercise']),
    }

    # 返回最大的值（临时方案）
    return max(values.values())


# 默认使用真实数据版本（使用飞书 API）
calculate_current_value = calculate_current_value_real


if __name__ == "__main__":
    # 测试：获取今天的记录
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    try:
        records = fetch_feishu_records(today_start, today_end)
        print(f"获取到 {len(records)} 条记录", file=sys.stderr)

        # 打印前3条记录用于调试
        for i, record in enumerate(records[:3]):
            print(f"记录 {i+1}: {record.get('fields', {})}")

        # 计算各类别时长
        print(f"\n工作时间: {calculate_category_duration(records, CATEGORY_MAPPINGS['work'])} 小时")
        print(f"创作时间: {calculate_category_duration(records, CATEGORY_MAPPINGS['creation'])} 小时")
        print(f"娱乐+放松时间: {calculate_category_duration(records, CATEGORY_MAPPINGS['entertainment'])} 小时")
        print(f"运动时间: {calculate_category_duration(records, CATEGORY_MAPPINGS['exercise'])} 小时")

    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
