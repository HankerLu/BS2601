#!/usr/bin/env python3
"""
对话流程管理脚本
提供对话流程引导和状态跟踪
"""

import json
import os
from datetime import datetime

# 获取脚本根目录
if '__file__' in dir():
    SCRIPTS_DIR = os.path.dirname(__file__)
else:
    SCRIPTS_DIR = os.path.join(os.getcwd(), 'scripts')

# 导入会话管理函数
exec(open(os.path.join(SCRIPTS_DIR, 'create_session.py')).read())
exec(open(os.path.join(SCRIPTS_DIR, 'identify_issues.py')).read())


class ConversationStage:
    """对话阶段枚举"""
    INITIAL = 'initial'           # 初始问题呈现
    PRIORITY_SELECTION = 'priority_selection'  # 优先级选择
    PROBLEM_DIAGNOSIS = 'problem_diagnosis'    # 问题诊断
    ROOT_CAUSE_ANALYSIS = 'root_cause_analysis'  # 根本原因分析
    SOLUTION_DISCUSSION = 'solution_discussion'  # 方案讨论
    ACTION_PLAN = 'action_plan'    # 行动计划
    SUMMARY = 'summary'            # 总结归档


class AnalysisMode:
    """分析模式枚举"""
    DEEP = 'deep'      # 深度模式：5 Whys
    QUICK = 'quick'    # 快速模式：2-3 轮对话


class ConversationFlow:
    """对话流程管理类"""

    def __init__(self, session_id, severity_level=None):
        self.session_id = session_id
        self.stage = ConversationStage.INITIAL
        self.substage = None  # 子阶段（如 root_cause_analysis 的具体轮次）
        self.severity_level = severity_level  # 'critical' | 'moderate' | 'mild'
        self.analysis_mode = AnalysisMode.DEEP if severity_level == 'critical' else AnalysisMode.QUICK
        self.selected_issue = None
        self.why_count = 0
        self.identified_causes = []
        self.proposed_solutions = []
        self.confirmed_actions = []

    def set_mode(self, mode):
        """
        设置分析模式

        Args:
            mode: 'deep' | 'quick'
        """
        self.analysis_mode = mode
        # 深度模式需要 5 Whys，快速模式只需 2-3 轮
        self.max_whys = 5 if mode == AnalysisMode.DEEP else 2

    def advance_stage(self, new_stage=None, substage=None):
        """
        推进到下一个阶段

        Args:
            new_stage: 新阶段（可选），如果不指定则自动推进
            substage: 子阶段（可选）
        """
        if new_stage:
            self.stage = new_stage
        if substage:
            self.substage = substage
        elif self.stage == ConversationStage.INITIAL:
            self.stage = ConversationStage.PRIORITY_SELECTION
        elif self.stage == ConversationStage.PRIORITY_SELECTION:
            self.stage = ConversationStage.PROBLEM_DIAGNOSIS
        elif self.stage == ConversationStage.PROBLEM_DIAGNOSIS:
            self.stage = ConversationStage.ROOT_CAUSE_ANALYSIS
        elif self.stage == ConversationStage.ROOT_CAUSE_ANALYSIS:
            # 检查是否完成了足够的 why 轮次
            if self.why_count >= self.max_whys:
                self.stage = ConversationStage.SOLUTION_DISCUSSION
            # 否则继续在同一阶段，增加 why_count
        elif self.stage == ConversationStage.SOLUTION_DISCUSSION:
            self.stage = ConversationStage.ACTION_PLAN
        elif self.stage == ConversationStage.ACTION_PLAN:
            self.stage = ConversationStage.SUMMARY

    def go_back(self):
        """回退到上一阶段"""
        stage_order = [
            ConversationStage.INITIAL,
            ConversationStage.PRIORITY_SELECTION,
            ConversationStage.PROBLEM_DIAGNOSIS,
            ConversationStage.ROOT_CAUSE_ANALYSIS,
            ConversationStage.SOLUTION_DISCUSSION,
            ConversationStage.ACTION_PLAN,
            ConversationStage.SUMMARY
        ]

        if self.stage in stage_order:
            current_index = stage_order.index(self.stage)
            if current_index > 0:
                self.stage = stage_order[current_index - 1]

    def add_cause(self, cause):
        """添加识别的原因"""
        self.identified_causes.append(cause)
        self.why_count += 1

    def add_solution(self, solution):
        """添加建议的解决方案"""
        self.proposed_solutions.append(solution)

    def add_action(self, action):
        """添加确认的行动项"""
        self.confirmed_actions.append(action)

    def get_state(self):
        """获取当前状态"""
        return {
            'stage': self.stage,
            'substage': self.substage,
            'severity_level': self.severity_level,
            'analysis_mode': self.analysis_mode,
            'selected_issue': self.selected_issue,
            'why_count': self.why_count,
            'max_whys': self.max_whys,
            'identified_causes': self.identified_causes,
            'proposed_solutions': self.proposed_solutions,
            'confirmed_actions': self.confirmed_actions
        }

    def should_continue_why(self):
        """判断是否应该继续问 why"""
        return self.why_count < self.max_whys


def generate_initial_prompt(issues):
    """
    生成初始问题呈现的提示词

    Args:
        issues: 识别的问题字典

    Returns:
        str: 提示词
    """
    if not issues['target_issues'] and not issues['status_issues']:
        return "目前没有发现需要分析的指标。你最近的表现看起来不错！继续保持。"

    lines = ["我发现以下指标存在问题：\n"]

    # Target Benchmark 问题
    if issues['target_issues']:
        lines.append("【严重问题】Target Benchmark")
        for issue in issues['target_issues']:
            lines.append(f"• {issue['name']}: 进度仅 {issue['progress']}%")
            lines.append(f"  目标 {issue['target_value']}{issue['unit']}，当前 {issue['current_value']}{issue['unit']}")
            lines.append(f"  截止日期: {issue['deadline']}，剩余 {issue['days_remaining']} 天")

    # Status Benchmark 问题
    if issues['status_issues']:
        lines.append("\n【问题】Status Benchmark")
        for issue in issues['status_issues']:
            lines.append(f"• {issue['name']}: 连续 {issue['consecutive_missed']} 次未达标")
            lines.append(f"  目标 {issue['comparison_type']} {issue['target_value']} {issue['unit']}")
            lines.append(f"  当前 {issue['current_value']} {issue['unit']}")

    # 询问优先级
    target_count = len(issues['target_issues'])
    status_count = len(issues['status_issues'])

    if target_count + status_count == 1:
        lines.append("\n我们从这个问题开始分析吧。")
    else:
        lines.append("\n你希望从哪个问题开始分析？")

    return "\n".join(lines)


def generate_diagnosis_prompt(issue, user_input, severity=None, mode='quick'):
    """
    生成问题诊断阶段的提示词

    Args:
        issue: 选中的问题字典
        user_input: 用户之前的输入
        severity: 问题严重程度 'critical' | 'moderate' | 'mild'
        mode: 分析模式 'deep' | 'quick'

    Returns:
        str: 提示词
    """
    # 根据严重程度调整开场
    if severity == 'critical':
        severity_desc = "【严重问题】"
        urgency = "这个情况比较紧急，我们需要尽快找到原因。"
    elif severity == 'moderate':
        severity_desc = "【中等问题】"
        urgency = "这个问题值得关注，我们来一起分析一下。"
    else:  # mild
        severity_desc = "【轻微问题】"
        urgency = "这个问题还不是很严重，不过我们可以讨论一下如何避免恶化。"

    # 根据模式调整深度
    if mode == 'deep':
        depth_desc = "我们会进行深入的分析，用5个'为什么'来挖掘根本原因。"
    else:  # quick
        depth_desc = "我们快速分析一下，找出主要原因就好。"

    if 'target' in str(issue.get('id', '')):
        # Target benchmark 问题
        return f"""
{severity_desc}我们来看【{issue['name']}】。

{urgency}
{depth_desc}

根据数据，你的进度只有 {issue['progress']}%。

{user_input}

你觉得是什么原因导致最近没有进展？我们可以从以下几个方面聊聊：
- 是否有记录每天的情况？
- 有没有遇到什么困难或阻碍？
- 最近的日常安排是怎样的？
"""
    else:
        # Status benchmark 问题
        return f"""
{severity_desc}我们来看【{issue['name']}】。

{urgency}
{depth_desc}

根据数据，你连续 {issue['consecutive_missed']} 次没有达标了。

{user_input}

你觉得是什么原因导致的？比如：
- 时间安排问题？
- 能力不足？
- 环境干扰？
- 动力不足？
"""


def generate_why_prompt(cause, why_count, max_whys=5):
    """
    生成 5 Whys 深入分析的提示词

    Args:
        cause: 用户提到的原因
        why_count: 已经问了几个 why
        max_whys: 最多问几个 why

    Returns:
        str: 提示词
    """
    remaining = max_whys - why_count

    if why_count < max_whys // 2:
        return f"""
明白了。那么「{cause}」又是由什么导致的？能不能具体讲讲？
（还需要 {remaining} 个深入问题）
"""
    elif why_count < max_whys:
        return f"""
我理解了。继续往深层想，「{cause}」背后更根本的原因是什么呢？
（还剩 {remaining} 个深入问题）
"""
    else:
        return f"""
好的，我想我已经理解核心问题了。

总结一下：你提到的关键原因是：「{cause}」

这是问题的根本原因吗？还是你觉得还有更深层的原因？
"""


def generate_solution_prompt(identified_causes):
    """
    生成方案讨论的提示词

    Args:
        identified_causes: 识别的原因列表

    Returns:
        str: 提示词
    """
    causes_text = "\n".join([f"• {cause}" for cause in identified_causes])

    return f"""
基于我们的分析，主要原因是：

{causes_text}

现在我们来讨论解决方案。我先说几个可能的方向：

1. **调整目标**：如果目标设定不合理，我们可以重新评估
2. **优化流程**：改进做事的方法和流程
3. **增加投入**：投入更多时间或资源
4. **环境优化**：减少干扰，创造更好的环境
5. **寻求支持**：获得他人的帮助或专业指导

你觉得哪个方向比较适合你？或者你有其他想法？
"""


def generate_action_plan_prompt(solutions, confirmed_actions):
    """
    生成行动计划的提示词

    Args:
        solutions: 讨论的解决方案列表
        confirmed_actions: 已确认的行动列表

    Returns:
        str: 提示词
    """
    if confirmed_actions:
        actions_text = "\n".join([f"• {action}" for action in confirmed_actions])
        return f"""
我们总结一下行动计划：

{actions_text}

这个方案你觉得可以吗？有没有需要调整的地方？
"""
    else:
        return f"""
让我帮你细化一下具体方案。

基于你选择的「{solutions[0] if solutions else '解决方案'}」，我们可以这样安排：

【本周】
• 具体行动1 - 预计耗时：X分钟/天
• 具体行动2 - 预计耗时：X分钟/天

【衡量标准】
• 可观察的结果

你觉得这个方案如何？我们可以根据你的情况调整。
"""


def generate_summary_prompt(issues, causes, actions):
    """
    生成总结的提示词

    Args:
        issues: 问题列表
        causes: 原因列表
        actions: 行动列表

    Returns:
        str: 提示词
    """
    lines = ["总结一下今天的讨论：\n"]

    # 问题描述
    if issues['target_issues']:
        for issue in issues['target_issues']:
            lines.append(f"【问题】{issue['name']}")
            lines.append(f"• 进度仅 {issue['progress']}%")
    if issues['status_issues']:
        for issue in issues['status_issues']:
            lines.append(f"【问题】{issue['name']}")
            lines.append(f"• 连续 {issue['consecutive_missed']} 次未达标")

    # 根本原因
    if causes:
        lines.append("\n【根本原因】")
        lines.extend([f"• {cause}" for cause in causes])

    # 行动计划
    if actions:
        lines.append("\n【行动计划】")
        lines.extend([f"• {action}" for action in actions])

    lines.append("\n【后续跟进】")
    lines.append("我会定期跟进进度。如果有任何问题，随时找我聊。")
    lines.append("\n加油！💪")

    return "\n".join(lines)


def create_analysis_session(trigger_source, trigger_reason, severity_level=None, analysis_mode='quick'):
    """
    创建完整的分析会话流程

    Args:
        trigger_source: 触发来源
        trigger_reason: 触发原因
        severity_level: 问题严重程度 'critical' | 'moderate' | 'mild'（可选）
        analysis_mode: 分析模式 'deep' | 'quick'（默认 'quick'）

    Returns:
        dict: 包含 session_id 和初始提示词的字典
    """
    # 识别问题（如果指定了严重程度，则过滤）
    severity_filter = 'critical' if analysis_mode == 'deep' else None
    issues = identify_all_issues(severity_filter=severity_filter)

    # 如果指定了严重程度且没有对应的问题，返回全部问题
    if severity_level and not issues['target_issues'] and not issues['status_issues']:
        issues = identify_all_issues()

    # 创建会话
    session_id = create_session(
        trigger_source=trigger_source,
        trigger_reason=trigger_reason,
        focus_area='both',
        issues_identified=issues,
        severity_level=severity_level,
        analysis_mode=analysis_mode
    )

    # 创建对话流程实例
    flow = ConversationFlow(session_id, severity_level=severity_level)
    flow.set_mode(analysis_mode)

    # 生成初始提示词
    initial_prompt = generate_initial_prompt(issues)

    # 记录初始消息
    add_message(
        session_id,
        role='assistant',
        content=initial_prompt,
        message_type='question'
    )

    return {
        'session_id': session_id,
        'flow': flow,
        'issues': issues,
        'initial_prompt': initial_prompt
    }


if __name__ == "__main__":
    # 测试：创建分析会话
    result = create_analysis_session(
        trigger_source='manual',
        trigger_reason='用户主动发起分析'
    )

    print(f"Session ID: {result['session_id']}")
    print(f"\nIssues: {json.dumps(result['issues'], indent=2)}")
    print(f"\nInitial Prompt:\n{result['initial_prompt']}")

    # 测试：生成诊断提示词
    if result['issues']['target_issues']:
        issue = result['issues']['target_issues'][0]
        diagnosis_prompt = generate_diagnosis_prompt(issue, "")
        print(f"\nDiagnosis Prompt:\n{diagnosis_prompt}")
