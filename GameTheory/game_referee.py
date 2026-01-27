from typing import Dict, Tuple, List

class GameReferee:
    """
    囚徒困境博弈的裁判/计分者。
    负责判定每轮得分、维护总分以及判定最终胜负。
    完全确定性的逻辑，不依赖 LLM。
    """
    def __init__(self, player1_name: str, player2_name: str, max_rounds: int = 5):
        self.p1_name = player1_name
        self.p2_name = player2_name
        self.max_rounds = max_rounds
        
        self.p1_score = 0
        self.p2_score = 0
        self.current_round = 0
        
        # 记录每轮的详细结果
        # 格式: {"round": 1, "p1_action": "cooperate", "p2_action": "defect", "p1_score": 0, "p2_score": 5}
        self.match_history: List[Dict] = []

    def judge_round(self, p1_action: str, p2_action: str) -> Tuple[int, int]:
        """
        判定一轮的得分。
        :param p1_action: 选手1的动作 ('cooperate' 或 'defect')
        :param p2_action: 选手2的动作 ('cooperate' 或 'defect')
        :return: (选手1本轮得分, 选手2本轮得分)
        """
        self.current_round += 1
        
        # 规范化输入
        a1 = p1_action.lower().strip()
        a2 = p2_action.lower().strip()
        
        s1 = 0
        s2 = 0
        
        # 计分逻辑
        if a1 == "cooperate" and a2 == "cooperate":
            # 互相合作：各得3分
            s1 = 3
            s2 = 3
        elif a1 == "defect" and a2 == "defect":
            # 互相背叛：各得1分
            s1 = 1
            s2 = 1
        elif a1 == "defect" and a2 == "cooperate":
            # P1背叛，P2合作：P1得5分，P2得0分
            s1 = 5
            s2 = 0
        elif a1 == "cooperate" and a2 == "defect":
            # P1合作，P2背叛：P1得0分，P2得5分
            s1 = 0
            s2 = 5
        else:
            # 异常情况处理（默认按双方背叛处理，或者抛出异常，这里选择保守给分0并打印警告）
            print(f"Warning: Invalid action(s) detected. P1: {a1}, P2: {a2}")
            s1 = 0
            s2 = 0

        # 更新总分
        self.p1_score += s1
        self.p2_score += s2
        
        # 记录历史
        record = {
            "round": self.current_round,
            "p1_action": a1,
            "p2_action": a2,
            "p1_score": s1,
            "p2_score": s2
        }
        self.match_history.append(record)
        
        return s1, s2

    def get_current_scores(self) -> Dict[str, int]:
        """返回当前总分"""
        return {
            self.p1_name: self.p1_score,
            self.p2_name: self.p2_score
        }

    def is_game_over(self) -> bool:
        """检查比赛是否结束"""
        return self.current_round >= self.max_rounds

    def get_final_result(self) -> Dict[str, Any]:
        """
        返回最终比赛结果报告
        """
        if not self.is_game_over():
             return {"status": "ongoing", "current_round": self.current_round}

        winner = "Draw"
        if self.p1_score > self.p2_score:
            winner = self.p1_name
        elif self.p2_score > self.p1_score:
            winner = self.p2_name

        return {
            "status": "finished",
            "total_rounds": self.current_round,
            "final_scores": {
                self.p1_name: self.p1_score,
                self.p2_name: self.p2_score
            },
            "winner": winner,
            "history": self.match_history
        }

# 简单的测试代码
if __name__ == "__main__":
    import json
    
    referee = GameReferee("PlayerA", "PlayerB", max_rounds=3)
    
    # Round 1: 合作 vs 合作
    print("--- Round 1 ---")
    s1, s2 = referee.judge_round("cooperate", "cooperate")
    print(f"Scores: {s1} - {s2}")
    
    # Round 2: 背叛 vs 合作
    print("--- Round 2 ---")
    s1, s2 = referee.judge_round("defect", "cooperate")
    print(f"Scores: {s1} - {s2}")
    
    # Round 3: 背叛 vs 背叛
    print("--- Round 3 ---")
    s1, s2 = referee.judge_round("defect", "defect")
    print(f"Scores: {s1} - {s2}")
    
    print("\n--- Final Result ---")
    print(json.dumps(referee.get_final_result(), indent=2))
