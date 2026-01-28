import json
from typing import List, Dict, Any
from llm_wraper import LLMWrapper

class PrisonerAgent:
    """
    参与囚徒困境博弈的智能体选手 (Player Agent)。
    基于 LLMWrapper 进行思考和决策。
    """
    def __init__(self, name: str, llm: LLMWrapper, max_rounds: int = 5):
        self.name = name
        self.llm = llm
        self.max_rounds = max_rounds
        self.history: List[Dict[str, Any]] = []
        
        # 定义博弈规则描述
        self.rules_description = f"""
【囚徒困境博弈规则 - 基础双人版】
你是一名参与囚徒困境博弈的选手。你的目标是在多轮博弈中尽可能获得更高的总分。

【重要】决策机制：
- 每一轮，你和对手必须**同时且独立**地做出选择，双方互不知晓对方的决策。
- 不存在任何先后顺序，也无法根据对方本轮的选择来调整自己的决策。
- 你只能基于前面几轮的记录来预测对手的行为模式，而无法看到对方当前轮次的选择。

每轮你需要在"合作"（不揭发）和"背叛"（揭发）之间做出选择。

得分规则如下：
1. 互相合作（两人都不揭发）：各得 3 分（双赢基础分）。
2. 互相背叛（两人互相揭发）：各得 1 分（重罚，双输最低分）。
3. 一方背叛，一方合作：
   - 背叛者（揭发的一方）得 5 分（最大收益，完胜）。
   - 合作者（被揭发的一方）得 0 分（最大亏损，完败）。

请基于博弈论逻辑、历史对手行为模式以及得分最大化原则进行思考。
一共有{self.max_rounds}轮博弈，{self.max_rounds}轮结束后定胜负。

【特别注意】
- 平局（例如两人总分相同）对你来说**不是**最优结果。你应该竭力争取让自己的总分**超过**对手。
- 如果在前面的轮次中比分一直胶着（例如一直合作导致分数相同），你必须考虑改变策略以打破僵局，争取利用对手的惯性思维来获取单轮最高分（5分），从而在总分上取得领先。
- 利益最大化意味着：既要追求高分，更要追求比对手更高的分数。完胜（我方背叛，对手合作）是拉开分差的最佳手段。
"""

    def update_history(self, round_num: int, my_action: str, opponent_action: str, my_score: int, opponent_score: int):
        """
        更新对局历史记录
        """
        record = {
            "round": round_num,
            "my_action": my_action,
            "opponent_action": opponent_action,
            "my_score": my_score,
            "opponent_score": opponent_score
        }
        self.history.append(record)

    def _get_current_total_scores(self) -> tuple[int, int]:
        """计算当前累计总分"""
        my_total = sum(r["my_score"] for r in self.history)
        opp_total = sum(r["opponent_score"] for r in self.history)
        return my_total, opp_total

    def _format_history(self) -> str:
        """
        将历史记录格式化为文本，供 Prompt 使用
        """
        if not self.history:
            return "目前是第一轮，暂无历史记录。当前比分: 0 vs 0。"
        
        lines = ["【历史对局记录】"]
        for record in self.history:
            lines.append(
                f"第 {record['round']} 轮: "
                f"我方选择[{record['my_action']}], 对手选择[{record['opponent_action']}] -> "
                f"得分: 我方 {record['my_score']}, 对手 {record['opponent_score']}"
            )
        
        my_total, opp_total = self._get_current_total_scores()
        lines.append(f"\n【当前实时总比分】 我方 {my_total} 分 vs 对手 {opp_total} 分")
        
        if my_total == opp_total:
            lines.append("当前局势：平局。请警惕！平局不是胜利，你需要尝试通过背叛来拉开差距。")
        elif my_total > opp_total:
            lines.append("当前局势：领先。请保持优势。")
        else:
            lines.append("当前局势：落后。你需要激进策略来反超。")
            
        return "\n".join(lines)

    def decide(self, current_round: int) -> Dict[str, Any]:
        """
        根据当前局势进行思考并作出决策。
        返回格式: {"thought": "思考过程...", "action": "cooperate" 或 "defect"}
        """
        history_str = self._format_history()
        
        system_prompt = f"""
{self.rules_description}

你需要输出一个 JSON 格式的决策结果。
JSON 格式要求：
{{
    "thought": "你的战术分析和思考过程，请结合当前总比分分析。如果是平局，请特别思考如何利用背叛（defect）来突袭对手以获得领先优势。",
    "action": "你的最终选择，必须是 'cooperate' (代表不揭发/合作) 或 'defect' (代表揭发/背叛) 其中之一"
}}
"""

        user_prompt = f"""
我是选手: {self.name}
当前是第 {current_round} 轮。

{history_str}

请根据历史记录分析对手的风格，并结合当前总比分做出本轮决策。
记住：你的目标是赢得比赛（总分高于对手），而不仅仅是合作共赢。如果一直平局，你将无法赢得比赛。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 调用 LLM 生成决策
        # 使用较低的 temperature 保证决策逻辑的一致性
        result = self.llm.generate_json(messages, temperature=0.3, mode=f"{self.name}_Round_{current_round}")

        # 容错处理：如果解析失败或格式不对，默认选择合作（或者根据需求设为背叛）
        # 这里我们做一个简单的结构校验
        if not result or "action" not in result:
            print(f"[{self.name}] 决策生成失败，启用默认策略(Cooperate)。原始返回: {result}")
            return {
                "thought": "LLM生成格式错误，执行默认策略。",
                "action": "cooperate"
            }
        
        # 归一化 action 值为小写
        result["action"] = result["action"].lower()
        if result["action"] not in ["cooperate", "defect"]:
             # 再次容错，如果输出了奇怪的词，倾向于保守策略（例如背叛以防守，或者合作）
             # 这里假设只识别 cooperate，其他都视为 defect 以防被利用
             if "cooperate" in result["action"] or "合作" in result["action"]:
                 result["action"] = "cooperate"
             else:
                 result["action"] = "defect"

        return result

# 简单的测试代码（如果直接运行此脚本）
if __name__ == "__main__":
    # 模拟两个 Agent 对战一局
    try:
        wrapper = LLMWrapper() # 需要环境变量中有 API KEY
        agent1 = PrisonerAgent("Agent A", wrapper)
        
        print(f"--- {agent1.name} 开始思考 ---")
        decision = agent1.decide(current_round=1)
        print(f"决策结果: {json.dumps(decision, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"测试运行出错: {e}")
        print("请确保已设置 ARK_API_KEY 环境变量，并且 llm_wraper.py 在同一目录下。")
