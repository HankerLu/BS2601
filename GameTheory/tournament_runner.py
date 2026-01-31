import json
import os
import time
import concurrent.futures
from itertools import combinations
from datetime import datetime
from collections import defaultdict

# 尝试导入
try:
    from llm_wraper import LLMWrapper
    from player_agent import PrisonerAgent
    from game_referee import GameReferee
except ImportError:
    pass # 允许在GUI中处理导入错误

class TournamentRunner:
    def __init__(self, log_callback=None, progress_callback=None):
        self.llm = LLMWrapper()
        self.log_callback = log_callback # func(msg)
        self.progress_callback = progress_callback # func(current, total)
        
        self.agent_keys = ["nice", "tit_for_tat", "opportunist", "absolutist", "machiavellian"]
        self.agent_info = {
            "nice": {"file": "nice_agent_config.json", "name": "Nice (老好人)"},
            "tit_for_tat": {"file": "tit_for_tat_agent_config.json", "name": "Tit-for-Tat (执法者)"},
            "opportunist": {"file": "opportunist_agent_config.json", "name": "Opportunist (机会主义者)"},
            "absolutist": {"file": "absolutist_agent_config.json", "name": "Absolutist (独裁者)"},
            "machiavellian": {"file": "machiavellian_agent_config.json", "name": "Machiavellian (权谋家)"}
        }
        
        self.available_agents = []
        self.match_results = []
        # 统计: total_score, matches_played, wins, losses, ties, cooperate_count, defect_count, betrayal_victim_count, betrayal_success_count
        self.stats = defaultdict(lambda: defaultdict(int))
        self.is_running = True

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    def load_agents(self):
        self.log("正在加载 Agent 配置...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.available_agents = []
        
        for key in self.agent_keys:
            info = self.agent_info[key]
            path = os.path.join(current_dir, info["file"])
            if os.path.exists(path):
                self.available_agents.append(key)
            else:
                self.log(f"Warning: 缺失配置文件 {info['file']}")
                
        if len(self.available_agents) < 2:
            self.log("错误: 可用选手不足 2 位")
            return False
        return True

    def stop(self):
        self.is_running = False

    def run_match(self, p1_key, p2_key, rounds=20):
        p1_name = self.agent_info[p1_key]["name"]
        p2_name = self.agent_info[p2_key]["name"]
        
        # 初始化
        p1 = PrisonerAgent(p1_name, self.llm, rounds, config_path=self.agent_info[p1_key]["file"])
        p2 = PrisonerAgent(p2_name, self.llm, rounds, config_path=self.agent_info[p2_key]["file"])
        referee = GameReferee(p1_name, p2_name, max_rounds=rounds)
        history = []
        
        for r in range(1, rounds + 1):
            if not self.is_running: break
            
            # 并发决策
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                f1 = executor.submit(p1.decide, r)
                f2 = executor.submit(p2.decide, r)
                try:
                    res1 = f1.result()
                    res2 = f2.result()
                except Exception as e:
                    self.log(f"Round {r} Error: {e}")
                    res1 = {"action": "cooperate"}
                    res2 = {"action": "cooperate"}
            
            act1 = res1.get("action", "cooperate")
            act2 = res2.get("action", "cooperate")
            s1, s2 = referee.judge_round(act1, act2)
            
            p1.update_history(r, act1, act2, s1, s2)
            p2.update_history(r, act2, act1, s2, s1)
            
            history.append({
                "round": r, "p1_action": act1, "p2_action": act2, 
                "p1_score": s1, "p2_score": s2
            })
            
            # 实时日志略微精简
            icon1 = "🟩" if act1.lower() == "cooperate" else "🟥"
            icon2 = "🟩" if act2.lower() == "cooperate" else "🟥"
            self.log(f"   R{r:02d}: {p1_name[:4]} {icon1} vs {icon2} {p2_name[:4]} -> {s1}:{s2}")
            
        final = referee.get_final_result()
        return {
            "p1_key": p1_key, "p2_key": p2_key, "p1_name": p1_name, "p2_name": p2_name,
            "rounds": rounds, "history": history, 
            "final_scores": final["final_scores"], "winner": final["winner"]
        }

    def update_stats(self, match_data):
        p1 = match_data["p1_key"]
        p2 = match_data["p2_key"]
        name1 = match_data["p1_name"]
        name2 = match_data["p2_name"]
        
        s1 = match_data["final_scores"].get(name1, 0)
        s2 = match_data["final_scores"].get(name2, 0)
        
        self.stats[p1]["total_score"] += s1
        self.stats[p2]["total_score"] += s2
        self.stats[p1]["matches_played"] += 1
        self.stats[p2]["matches_played"] += 1
        
        if s1 > s2:
            self.stats[p1]["wins"] += 1; self.stats[p2]["losses"] += 1
        elif s2 > s1:
            self.stats[p2]["wins"] += 1; self.stats[p1]["losses"] += 1
        else:
            self.stats[p1]["ties"] += 1; self.stats[p2]["ties"] += 1

        for r in match_data["history"]:
            a1 = r["p1_action"].lower() == "cooperate"
            a2 = r["p2_action"].lower() == "cooperate"
            
            self.stats[p1]["cooperate_count" if a1 else "defect_count"] += 1
            self.stats[p2]["cooperate_count" if a2 else "defect_count"] += 1
            
            if a1 and not a2: # p1 被坑
                self.stats[p1]["betrayal_victim_count"] += 1
                self.stats[p2]["betrayal_success_count"] += 1
            elif not a1 and a2: # p1 背刺
                self.stats[p1]["betrayal_success_count"] += 1
                self.stats[p2]["betrayal_victim_count"] += 1

    def run_tournament(self, rounds_per_match=20):
        self.log(f"🏁 启动循环赛 (每场 {rounds_per_match} 轮)")
        if not self.available_agents:
            if not self.load_agents(): return

        matchups = list(combinations(self.available_agents, 2))
        total_matches = len(matchups)
        self.log(f"📅 共 {total_matches} 场比赛")
        
        for i, (p1, p2) in enumerate(matchups):
            if not self.is_running: break
            
            if self.progress_callback:
                self.progress_callback(i, total_matches)
                
            n1 = self.agent_info[p1]["name"]
            n2 = self.agent_info[p2]["name"]
            self.log(f"\n--- 比赛 {i+1}/{total_matches}: {n1} vs {n2} ---")
            
            match_data = self.run_match(p1, p2, rounds_per_match)
            self.match_results.append(match_data)
            self.update_stats(match_data)
            
            s1 = match_data['final_scores'][match_data['p1_name']]
            s2 = match_data['final_scores'][match_data['p2_name']]
            self.log(f"🏆 比赛结束: {s1} : {s2}")
            
            time.sleep(1) # 冷却

        if self.progress_callback:
            self.progress_callback(total_matches, total_matches)
        
        self.log("\n✅ 循环赛全部结束！")
        self.generate_report()

    def generate_report(self):
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("api_logs", exist_ok=True)
        filename = f"api_logs/tournament_report_{timestamp_str}.md"
        
        self.log(f"正在生成报告: {filename}")
        display_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines = [
            f"# 🏰 黑暗森林生存实验报告",
            f"> 时间: {display_time} | 场次: {len(self.match_results)}",
            "",
            "## 🏆 生存积分榜",
            "| 排名 | 选手 | 总分 | 胜/平/负 | 背叛率 | 被坑 | 背刺 |",
            "|---|---|---|---|---|---|---|"
        ]
        
        sorted_stats = sorted(self.stats.items(), key=lambda x: x[1]["total_score"], reverse=True)
        for rank, (key, d) in enumerate(sorted_stats, 1):
            name = self.agent_info[key]["name"]
            total_moves = d["cooperate_count"] + d["defect_count"]
            rate = (d["defect_count"]/total_moves*100) if total_moves else 0
            lines.append(f"| {rank} | **{name}** | **{d['total_score']}** | {d['wins']}/{d['ties']}/{d['losses']} | {rate:.1f}% | {d['betrayal_victim_count']} | {d['betrayal_success_count']} |")
            
        lines.append("\n## ⚔️ 详细战况")
        for m in self.match_results:
            p1 = m["p1_name"]; p2 = m["p2_name"]
            s1 = m["final_scores"][p1]; s2 = m["final_scores"][p2]
            lines.append(f"### {p1} ({s1}) vs {p2} ({s2})")
            lines.append("| R | P1 | P2 | Score |")
            lines.append("|---|:---:|:---:|:---:|")
            for r in m["history"]:
                i1 = "🟩" if r["p1_action"].lower()=="cooperate" else "🟥"
                i2 = "🟩" if r["p2_action"].lower()=="cooperate" else "🟥"
                lines.append(f"| {r['round']} | {i1} | {i2} | {r['p1_score']}:{r['p2_score']} |")
            lines.append("")
            
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        self.log("报告已生成。")

if __name__ == "__main__":
    runner = TournamentRunner()
    runner.run_tournament(5)
