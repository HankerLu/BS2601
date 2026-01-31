import argparse
import sys
import os
import concurrent.futures
import json
import time

# Ensure we can import modules from the GameTheory directory
# This script is expected to be run from the root or GameTheory directory
sys.path.append(os.getcwd())
if os.path.join(os.getcwd(), 'GameTheory') not in sys.path:
    sys.path.append(os.path.join(os.getcwd(), 'GameTheory'))

try:
    from GameTheory.llm_wraper import LLMWrapper
    from GameTheory.player_agent import PrisonerAgent
    from GameTheory.game_referee import GameReferee
except ImportError:
    try:
        # Fallback if run directly inside GameTheory
        from llm_wraper import LLMWrapper
        from player_agent import PrisonerAgent
        from game_referee import GameReferee
    except ImportError as e:
        print(f"Error: Could not import required modules. {e}")
        print("Please run this script from the workspace root.")
        sys.exit(1)

def run_duel(player_config, npc_config, rounds=10):
    print(f"Initializing Duel...")
    try:
        llm = LLMWrapper()
    except Exception as e:
        print(f"Failed to initialize LLM: {e}")
        return

    # Helper to load name from config if possible, else default
    def get_agent_name(path, default):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # The config file structure in this project doesn't strictly have a 'name' field 
                # (names are usually passed to constructor), but we can try to infer or use filename
                pass
        except:
            pass
        return default

    p1_name = "New Agent"
    p2_name = "NPC Agent"
    
    # Resolve paths
    if not os.path.exists(player_config):
        print(f"Error: Player config not found at {player_config}")
        return
    if not os.path.exists(npc_config):
        # Try finding in GameTheory folder
        alt_npc = os.path.join("GameTheory", npc_config)
        if os.path.exists(alt_npc):
            npc_config = alt_npc
        else:
            print(f"Error: NPC config not found at {npc_config}")
            return

    print(f"Player Config: {player_config}")
    print(f"NPC Config: {npc_config}")

    p1 = PrisonerAgent(p1_name, llm, rounds, config_path=player_config)
    p2 = PrisonerAgent(p2_name, llm, rounds, config_path=npc_config)
    referee = GameReferee(p1_name, p2_name, max_rounds=rounds)
    
    print(f"\n🔥🔥 DUEL START: {p1_name} vs {p2_name} ({rounds} Rounds) 🔥🔥\n")
    
    history_table = []
    
    for r in range(1, rounds + 1):
        print(f"--- Round {r}/{rounds} ---")
        
        # Parallel decision making
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(p1.decide, r)
            f2 = executor.submit(p2.decide, r)
            try:
                res1 = f1.result()
                res2 = f2.result()
            except Exception as e:
                print(f"Error during decision: {e}")
                res1 = {"action": "cooperate", "thought": "Error"}
                res2 = {"action": "cooperate", "thought": "Error"}

        act1 = res1.get("action", "cooperate")
        act2 = res2.get("action", "cooperate")
        
        # Display thoughts (briefly)
        print(f"[{p1_name}]: {res1.get('thought', '')[:100]}...")
        # print(f"[{p2_name}]: {res2.get('thought', '')[:100]}...")
        
        # Referee judge
        s1, s2 = referee.judge_round(act1, act2)
        
        # Update history
        p1.update_history(r, act1, act2, s1, s2)
        p2.update_history(r, act2, act1, s2, s1)
        
        # Visual output
        icon1 = "🟩" if act1.lower() == "cooperate" else "🟥"
        icon2 = "🟩" if act2.lower() == "cooperate" else "🟥"
        print(f"Result: {icon1} vs {icon2} -> Scores: +{s1} / +{s2}")
        
        history_table.append([r, act1, act2, s1, s2])
        time.sleep(1)

    # Final results
    final = referee.get_final_result()
    print("\n" + "="*30)
    print(f"🏆 FINAL RESULT: {final['winner']}")
    print(f"Scores: {final['final_scores']}")
    print("="*30)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a prisoner's dilemma duel.")
    parser.add_argument("--player-config", required=True, help="Path to the new agent's config file")
    parser.add_argument("--npc-config", default="GameTheory/tit_for_tat_agent_config.json", help="Path to the NPC's config file")
    parser.add_argument("--rounds", type=int, default=10, help="Number of rounds to play")
    
    args = parser.parse_args()
    
    run_duel(args.player_config, args.npc_config, args.rounds)
