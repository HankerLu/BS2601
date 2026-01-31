import json
import os
from typing import List, Dict, Any
from llm_wraper import LLMWrapper

class PrisonerAgent:
    """
    参与囚徒困境博弈的智能体选手 (Player Agent)。
    基于 LLMWrapper 进行思考和决策。
    """
    def __init__(self, name: str, llm: LLMWrapper, max_rounds: int = 5, config_path: str = "opportunist_agent_config.json"):
        self.name = name
        self.llm = llm
        self.max_rounds = max_rounds
        self.history: List[Dict[str, Any]] = []
        
        # 加载配置
        self.config = self._load_config(config_path)

    def _load_config(self, path: str) -> Dict[str, Any]:
        """加载 Agent 配置文件"""
        # 如果路径是相对路径，尝试基于当前工作目录查找
        if os.path.exists(path):
            abs_path = path
        else:
            # 尝试在当前脚本目录下查找
            current_dir = os.path.dirname(os.path.abspath(__file__))
            abs_path = os.path.join(current_dir, path)
            
        if not os.path.exists(abs_path):
            print(f"Warning: Config file {path} not found at {abs_path}. Using empty config.")
            # 这里可以考虑返回一个硬编码的默认配置，以防文件丢失导致程序崩溃
            # 为了简单起见，这里假设文件一定存在或由外部保证
            return {}
            
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

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
        
        # 使用配置中的策略指导
        guidance = self.config.get("strategy_guidance", {})
        if my_total == opp_total:
            lines.append(guidance.get("tie", ""))
        elif my_total > opp_total:
            lines.append(guidance.get("lead", ""))
        else:
            lines.append(guidance.get("lag", ""))
            
        return "\n".join(lines)

    def decide(self, current_round: int) -> Dict[str, Any]:
        """
        根据当前局势进行思考并作出决策。
        返回格式: {"thought": "思考过程...", "action": "cooperate" 或 "defect"}
        """
        history_str = self._format_history()
        
        # 构造 System Prompt
        # 填充 max_rounds 参数
        rules_desc = self.config.get("rules_description", "").format(max_rounds=self.max_rounds)
        json_instr = self.config.get("json_format_instruction", "")
        
        system_prompt = f"{rules_desc}\n\n{json_instr}"

        # 构造 User Prompt
        # 填充 name, current_round, history_str 参数
        user_prompt_template = self.config.get("user_prompt_template", "")
        user_prompt = user_prompt_template.format(
            name=self.name,
            current_round=current_round,
            history_str=history_str
        )
        
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
        # 确保 opportunistic_agent_config.json 存在
        # 如果需要测试不同配置，可以指定 config_path
        agent1 = PrisonerAgent("Agent A", wrapper, config_path="opportunist_agent_config.json")
        
        print(f"--- {agent1.name} 开始思考 ---")
        decision = agent1.decide(current_round=1)
        print(f"决策结果: {json.dumps(decision, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"测试运行出错: {e}")
        print("请确保已设置 ARK_API_KEY 环境变量，并且 llm_wraper.py 在同一目录下。")
