# Goal Execution Coach Skills

此目录包含 GoalExecutionCoach workspace 的所有技能。

## 技能结构规范

每个技能应遵循以下结构：

```
skill-name/
├── SKILL.md         # 必需：技能定义文件
├── scripts/         # 可选：Python/Shell脚本
│   └── main.py
├── tests/          # 可选：测试用例
└── references/     # 可选：参考资料
```

## 添加新技能

1. 在此目录下创建新的技能文件夹
2. 创建 `SKILL.md` 定义文件
3. 根据需要添加脚本和测试
4. 技能将在workspace内立即可用

## 注意事项

- 此workspace的技能不会与全局技能混淆
- 技能名称在workspace内应保持唯一
- 测试技能时请确保在 `GoalExecutionCoach/` 目录下运行
