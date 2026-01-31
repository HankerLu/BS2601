---
name: game-theory-duel
description: Create a new prisoner's dilemma agent and duel with an official NPC agent (Tit-for-Tat). Use when testing new strategies or creating agents.
---

# Game Theory Duel

## Instructions

Follow these steps to create a new agent and test it against a standard NPC.

### 1. Create Agent Configuration

Ask the user for the agent's strategy description. Then create a new JSON config file (e.g., `GameTheory/my_agent_config.json`) based on the template below.

**Template Structure:**
```json
{
  "rules_description": "Describe the agent's core values and personality.",
  "json_format_instruction": "Standard JSON output format instructions.",
  "user_prompt_template": "Prompt template for the LLM, including {name}, {current_round}, {history_str}.",
  "strategy_guidance": {
    "tie": "Strategy when scores are tied.",
    "lead": "Strategy when leading.",
    "lag": "Strategy when losing."
  }
}
```

(See `.cursor/skills/game-theory-duel/templates/agent_template.json` for the full template)

### 2. Run the Duel

Use the provided script to run a 10-round duel against the Tit-for-Tat (NPC) agent.

```bash
python .cursor/skills/game-theory-duel/scripts/duel_runner.py \
  --player-config "GameTheory/your_new_agent.json" \
  --npc-config "GameTheory/tit_for_tat_agent_config.json" \
  --rounds 10
```

## Examples

**User:** "Create a Grudger agent that cooperates until betrayed once, then defects forever."

**Agent Action:**
1. Create `GameTheory/grudger_config.json` with appropriate description and prompts.
2. Run:
   ```bash
   python .cursor/skills/game-theory-duel/scripts/duel_runner.py --player-config GameTheory/grudger_config.json
   ```

## Notes

- The NPC defaults to `tit_for_tat_agent_config.json` but can be changed via `--npc-config`.
- Ensure `llm_wraper.py` and `player_agent.py` are accessible (the script handles `sys.path` for `GameTheory/`).
