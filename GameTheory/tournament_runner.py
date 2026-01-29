import json
import os
import time
import itertools
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Any, Tuple

# 导入现有模块
# 假设这些文件在同一目录下
from llm_wraper import LLMWrapper
from player_agent import PrisonerAgent
from game_referee import GameReferee

class TournamentRunner:
    def __init__(self, match_rounds: int = 20):
        self.match_rounds = match_rounds
        self.agents_config = {}
        self.results = []
        self.llm = None
        self.stats = {}

    def load_configs(self):
        """自动加载当前目录下的 5 个特定配置文件"""
        config_files = {
            "Nice": "nice_agent_config.json",
            "Tit-for-Tat": "tit_for_tat_agent_config.json",
            "Opportunist": "opportunist_agent_config.json",
            "Absolutist": "absolutist_agent_config.json",
            "Machiavellian": "machiavellian_agent_config.json"
        }
        
        print("正在加载 Agent 配置文件...")
        for name, filename in config_files.items():
            if os.path.exists(filename):
                self.agents_config[name] = filename
                print(f"  [OK] {name} -> {filename}")
            else:
                print(f"  [ERROR] {name} 配置文件 {filename} 未找到！")
        
        if len(self.agents_config) < 2:
            raise Exception("有效的 Agent 配置少于 2 个，无法进行循环赛。")

    def initialize_llm(self):
        """初始化 LLM Wrapper"""
        try:
            self.llm = LLMWrapper()
            print("LLM 初始化成功。")
        except Exception as e:
            print(f"LLM 初始化失败: {e}")
            raise

    def run_match(self, p1_name: str, p2_name: str) -> Dict[str, Any]:
        """执行一场 A vs B 的比赛"""
        print(f"\n>>> 开始比赛: {p1_name} vs {p2_name} (共 {self.match_rounds} 轮) <<<")
        
        p1_config = self.agents_config[p1_name]
        p2_config = self.agents_config[p2_name]
        
        # 实例化 Agent 和 裁判
        # 注意：每次比赛都需要重新实例化 Agent，以清除记忆
        agent1 = PrisonerAgent(p1_name, self.llm, self.match_rounds, config_path=p1_config)
        agent2 = PrisonerAgent(p2_name, self.llm, self.match_rounds, config_path=p2_config)
        referee = GameReferee(p1_name, p2_name, max_rounds=self.match_rounds)
        
        match_log = []
        
        for r in range(1, self.match_rounds + 1):
            # 并发调用 LLM 进行决策
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(agent1.decide, r)
                future2 = executor.submit(agent2.decide, r)
                
                try:
                    res1 = future1.result()
                    res2 = future2.result()
                except Exception as e:
                    print(f"  [Round {r}] LLM 调用出错: {e}")
                    # 出错时默认合作，避免崩溃
                    res1 = {"action": "cooperate", "thought": "Error"}
                    res2 = {"action": "cooperate", "thought": "Error"}
            
            act1 = res1.get("action", "cooperate")
            act2 = res2.get("action", "cooperate")
            thought1 = res1.get("thought", "")
            thought2 = res2.get("thought", "")
            
            # 裁判判分
            score1, score2 = referee.judge_round(act1, act2)
            
            # 更新记忆
            agent1.update_history(r, act1, act2, score1, score2)
            agent2.update_history(r, act2, act1, score2, score1)
            
            # 记录本轮日志
            print(f"  Round {r}: {p1_name}[{act1}] {score1} : {score2} {p2_name}[{act2}]")
            
            match_log.append({
                "round": r,
                "p1": p1_name, "p2": p2_name,
                "a1": act1, "a2": act2,
                "s1": score1, "s2": score2,
                "t1": thought1, "t2": thought2
            })
            
            # 简单延时防止速率限制
            time.sleep(1)

        final_res = referee.get_final_result()
        return {
            "players": (p1_name, p2_name),
            "final_scores": final_res["final_scores"],
            "winner": final_res["winner"],
            "history": match_log
        }

    def run_tournament(self):
        """执行单循环赛"""
        if not self.llm:
            self.initialize_llm()
            
        agent_names = list(self.agents_config.keys())
        # 生成两两组合 (不分主客场，即 A vs B 和 B vs A 视为同一场组合，但为了公平，通常循环赛 A vs B 即可)
        # 这里使用 itertools.combinations 生成唯一的配对
        pairs = list(itertools.combinations(agent_names, 2))
        
        print(f"即将开始循环赛，共 {len(pairs)} 场比赛。")
        
        for i, (p1, p2) in enumerate(pairs, 1):
            print(f"--- 进度 {i}/{len(pairs)} ---")
            match_data = self.run_match(p1, p2)
            self.results.append(match_data)
            
            # 比赛间歇
            time.sleep(2)

    def analyze_data(self):
        """统计各项指标"""
        # 初始化统计表
        stats = {name: {
            "total_score": 0,
            "matches_played": 0,
            "betrayal_count": 0, # 背叛次数
            "total_actions": 0,
            "sucker_count": 0,   # 被剥削次数 (我合作，你背叛)
            "first_blood": 0,    # 率先背叛次数 (从合作转背叛)
            "blacken_round": []  # 黑化轮次记录
        } for name in self.agents_config.keys()}
        
        for match in self.results:
            p1, p2 = match["players"]
            history = match["history"]
            
            # 更新总分
            stats[p1]["total_score"] += match["final_scores"][p1]
            stats[p2]["total_score"] += match["final_scores"][p2]
            stats[p1]["matches_played"] += 1
            stats[p2]["matches_played"] += 1
            
            # 分析每场比赛的细节
            p1_betrayed_first = False
            p2_betrayed_first = False
            
            for r_data in history:
                a1 = r_data["a1"].lower()
                a2 = r_data["a2"].lower()
                
                # 统计背叛率
                stats[p1]["total_actions"] += 1
                stats[p2]["total_actions"] += 1
                if a1 == "defect": stats[p1]["betrayal_count"] += 1
                if a2 == "defect": stats[p2]["betrayal_count"] += 1
                
                # 统计被剥削 (Sucker: C vs D)
                if a1 == "cooperate" and a2 == "defect":
                    stats[p1]["sucker_count"] += 1
                if a2 == "cooperate" and a1 == "defect":
                    stats[p2]["sucker_count"] += 1
                    
                # 统计第一滴血 (前一轮还是和谐的/或者是第一轮，突然有人背叛)
                # 简化定义：只要之前的轮次双方都是 cooperate (或者第一轮)，这一轮谁 defect 了
                # 这里我们需要更严谨的逻辑：如果直到第 N 轮才出现第一个 defect
                # 检查是否是本场比赛的第一个背叛行为
                is_first_betrayal_of_match = True
                for prev_r in history[:r_data["round"]-1]:
                    if prev_r["a1"].lower() == "defect" or prev_r["a2"].lower() == "defect":
                        is_first_betrayal_of_match = False
                        break
                
                if is_first_betrayal_of_match:
                    if a1 == "defect" and a2 == "cooperate":
                        stats[p1]["first_blood"] += 1
                        # 记录 Nice 的黑化? (如果 p1 是 Nice)
                        if p1 == "Nice": stats[p1]["blacken_round"].append(r_data["round"])
                    elif a2 == "defect" and a1 == "cooperate":
                        stats[p2]["first_blood"] += 1
                        if p2 == "Nice": stats[p2]["blacken_round"].append(r_data["round"])
                    elif a1 == "defect" and a2 == "defect":
                        # 同时背叛，都算
                        stats[p1]["first_blood"] += 1
                        stats[p2]["first_blood"] += 1

        self.stats = stats

    def generate_markdown_report(self, filename="tournament_report.md"):
        """生成 Markdown 战报"""
        if not self.stats:
            self.analyze_data()
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        md = f"# 🏰 黑暗森林生存实验战报\n\n"
        md += f"**生成时间**: {timestamp}\n"
        md += f"**赛制**: 5 名 Agent 单循环赛，每场 {self.match_rounds} 轮\n\n"
        
        # 1. 积分排行榜
        md += "## 🏆 最终积分榜\n\n"
        md += "| 排名 | 选手 | 总得分 | 场均得分 | 胜率 |\n"
        md += "|---|---|---|---|---|\n"
        
        sorted_players = sorted(self.stats.items(), key=lambda x: x[1]["total_score"], reverse=True)
        
        for rank, (name, data) in enumerate(sorted_players, 1):
            avg_score = data["total_score"] / (data["matches_played"] * self.match_rounds) if data["matches_played"] else 0
            # 胜率计算稍微麻烦点，这里先简单展示总分
            md += f"| {rank} | **{name}** | {data['total_score']} | {avg_score:.2f} | -\n"
            
        md += "\n---\n\n"
        
        # 2. 性格侧写分析
        md += "## 🧠 性格侧写分析\n\n"
        md += "| 选手 | 背叛率 (Betrayal Rate) | 被剥削指数 (Sucker Index) | 第一滴血 (First Blood) |\n"
        md += "|---|---|---|---|\n"
        
        for name, data in self.stats.items():
            b_rate = (data["betrayal_count"] / data["total_actions"] * 100) if data["total_actions"] else 0
            md += f"| {name} | {b_rate:.1f}% | {data['sucker_count']} 次 | {data['first_blood']} 次 |\n"
            
        md += "\n---\n\n"
        
        # 3. 精彩对局回放 (Highlights)
        md += "## ⚔️ 精彩对局回放\n\n"
        
        for match in self.results:
            p1, p2 = match["players"]
            s1 = match["final_scores"][p1]
            s2 = match["final_scores"][p2]
            
            md += f"### {p1} vs {p2} ({s1} : {s2})\n\n"
            
            # 寻找关键转折点
            # 比如: 第一轮, 最后一轮, 以及第一次背叛的轮次
            history = match["history"]
            key_rounds = [history[0], history[-1]] # 首尾
            
            # 找第一次背叛
            first_betray_idx = -1
            for i, h in enumerate(history):
                if h["a1"].lower() == "defect" or h["a2"].lower() == "defect":
                    first_betray_idx = i
                    break
            
            if first_betray_idx != -1 and first_betray_idx != 0 and first_betray_idx != len(history)-1:
                key_rounds.insert(1, history[first_betray_idx])
                
            # 去重并排序
            key_rounds = sorted({h["round"]: h for h in key_rounds}.values(), key=lambda x: x["round"])
            
            for h in key_rounds:
                emoji1 = "🤝" if h["a1"].lower() == "cooperate" else "🔪"
                emoji2 = "🤝" if h["a2"].lower() == "cooperate" else "🔪"
                
                md += f"- **Round {h['round']}**: {p1} {emoji1} vs {emoji2} {p2} \n"
                md += f"  - *{p1}*: \"{h['t1'][:50]}...\"\n"
                md += f"  - *{p2}*: \"{h['t2'][:50]}...\"\n"
            
            md += "\n"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(md)
        
        print(f"战报已生成: {filename}")

if __name__ == "__main__":
    runner = TournamentRunner(match_rounds=10) # 测试用 10 轮
    runner.load_configs()
    try:
        runner.run_tournament()
        runner.generate_markdown_report()
    except Exception as e:
        print(f"运行出错: {e}")
