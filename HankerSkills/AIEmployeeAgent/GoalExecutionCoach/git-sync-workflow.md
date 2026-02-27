# Skill 同步工作流文档

本文档描述如何在本地 Claude Code 和远程 OpenClaw 服务器之间管理 skill 的变更同步。

## 架构设计

### 分支策略
```
main          # 稳定版本，直接部署到 OpenClaw
dev           # 本地 Claude Code 开发分支
bugfix-*      # OpenClaw 使用时发现的问题修复
```

### 工作流程概览
```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│  Claude Code    │  Git    │   GitHub     │  自动   │   OpenClaw      │
│  (本地开发)      │ <----> │  (代码仓库)   │ ---->  │   (服务器)       │
└─────────────────┘         └──────────────┘         └─────────────────┘
      dev 分支                   main 分支               main 分支
```

---

## 本地（Claude Code 环境）操作

### 初始化阶段（一次性）

```bash
# 进入 skill 目录
cd /Users/hankerlu/Desktop/BS2601/HankerSkills/AIEmployeeAgent/GoalExecutionCoach

# 检查是否已经是 git 仓库
git status

# 如果没有远程仓库，先在 GitHub 创建，然后关联
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 确保当前是 main 分支
git checkout main

# 推送现有内容
git push -u origin main
```

### 创建分支结构（一次性）

```bash
# 创建并切换到 dev 分支
git checkout -b dev
git push -u origin dev

# 查看分支
git branch -a
```

### 日常开发操作

```bash
# 1. 开发前同步最新代码
git checkout dev
git pull origin dev

# 2. 编辑 skill 文件（用 Claude Code）

# 3. 提交变更
git add .claude/skills/status-benchmark-manage/
git commit -m "feat: add new feature"

# 4. 推送
git push origin dev

# 5. 合并到 main（部署到服务器）
git checkout main
git merge dev
git push origin main
# 这会触发自动部署到服务器
```

### 开发时处理冲突

```bash
# 在合并到 main 前先 pull main
git checkout dev
git pull origin main

# 如果有冲突，解决后
git add .
git commit -m "resolve merge conflicts"

# 然后合并到 main
git checkout main
git merge dev
git push origin main
```

---

## 服务器（OpenClaw 环境）操作

### 初始化阶段（一次性）

```bash
# SSH 登录服务器
ssh user@your-server

# 进入 OpenClaw 的 skills 目录
cd /path/to/openclaw/skills

# 克隆仓库
git clone https://github.com/你的用户名/你的仓库名.git

# 进入项目目录
cd 你的仓库名
```

### 配置技能目录（一次性）

根据 OpenClaw 的目录结构，建立符号链接：

```bash
# 方案1：符号链接（推荐，自动同步）
ln -s /path/to/你的仓库名/.claude/skills/status-benchmark-manage \
      /path/to/openclaw/skills/status-benchmark-manage

ln -s /path/to/你的仓库名/.claude/skills/target-benchmark-manage \
      /path/to/openclaw/skills/target-benchmark-manage

# 方案2：复制（需要手动更新）
# cp -r .claude/skills/status-benchmark-manage \
#   /path/to/openclaw/skills/
```

### 日常更新操作

```bash
# 1. 进入项目目录
cd /path/to/你的仓库名

# 2. 拉取最新代码
git pull origin main

# 3. 重启 OpenClaw 或重新加载 skills（根据 OpenClaw 的机制）
# 例如：
# systemctl restart openclaw
# 或
# openclaw reload-skills
```

### 服务器上发现问题时（Hotfix 流程）

```bash
# 1. 进入项目目录
cd /path/to/你的仓库名

# 2. 确保在最新代码
git pull origin main

# 3. 创建 hotfix 分支
git checkout -b bugfix/fix-issue-2025-02-27

# 4. 直接修改文件
vim .claude/skills/status-benchmark-manage/SKILL.md

# 5. 提交
git add .
git commit -m "fix: correct field mapping issue"

# 6. 推送
git push origin bugfix/fix-issue-2025-02-27

# 7. 回到 main 分支，合并 hotfix
git checkout main
git merge bugfix/fix-issue-2025-02-27
git push origin main

# 8. 可选：删除 hotfix 分支
git branch -d bugfix/fix-issue-2025-02-27
git push origin --delete bugfix/fix-issue-2025-02-27
```

### 设置自动拉取（可选）

```bash
# 编辑 crontab
crontab -e

# 添加每小时自动拉取一次
0 * * * * cd /path/to/你的仓库名 && /usr/bin/git pull origin main >> /var/log/skill-update.log 2>&1

# 或者添加每天晚上 2 点自动拉取
0 2 * * * cd /path/to/你的仓库名 && /usr/bin/git pull origin main && /path/to/openclaw/reload-skills.sh >> /var/log/skill-update.log 2>&1
```

---

## 操作场景对照表

| 操作场景 | 本地 Claude Code | 服务器 OpenClaw |
|---------|----------------|-----------------|
| **初始化** | git init, git remote add, git push | git clone, 建立符号链接 |
| **正常更新** | git pull, 编辑, git push | git pull |
| **新功能开发** | dev 分支开发 → merge 到 main | 不涉及 |
| **紧急修复** | 直接在 dev 修复 | 创建 bugfix 分支 → merge 到 main |
| **触发部署** | push 到 main | - |
| **处理冲突** | git pull origin main，解决冲突后 merge | git pull origin main，解决冲突 |

---

## 最佳实践

### Commit Message 规范

```bash
# 新功能
git commit -m "feat: add weight tracking feature"

# 修复问题
git commit -m "fix: correct database connection error"

# 文档更新
git commit -m "docs: update README with sync workflow"

# 重构
git commit -m "refactor: simplify skill loading logic"

# 性能优化
git commit -m "perf: reduce database query time"
```

### 本地开发检查清单

- [ ] 切换到 dev 分支
- [ ] 拉取最新代码
- [ ] 完成开发
- [ ] 提交变更
- [ ] 推送到 dev
- [ ] 合并到 main（触发部署）

### 服务器修复检查清单

- [ ] 创建 bugfix 分支
- [ ] 修复问题
- [ ] 提交并推送
- [ ] 合并到 main
- [ ] 验证修复效果
- [ ] 清理 bugfix 分支

### 冲突预防

1. 本地开发前先 `git pull origin dev`
2. 合并到 main 前先 `git pull origin main`
3. 大改动前通知其他开发者
4. 及时处理合并冲突

---

## 快捷命令别名（可选）

### 本地 Git 别名

在 `~/.gitconfig` 中添加：

```ini
[alias]
    # 快速同步和推送
    dev-sync = "!f() { git checkout dev && git pull origin dev; }; f"
    dev-push = "!f() { git add . && git commit -m \"$1\" && git push origin dev; }; f"
    deploy = "!f() { git checkout main && git merge dev && git push origin main; }; f"

    # 快速查看分支
    branches = branch -a

    # 快速查看状态
    st = status
```

使用示例：
```bash
git dev-sync          # 同步 dev 分支
git dev-push "add feature"  # 提交并推送
git deploy            # 部署到 main
```

### 服务器快捷脚本

创建 `/usr/local/bin/skill-fix.sh`：

```bash
#!/bin/bash
REPO_PATH="/path/to/你的仓库名"
BRANCH_NAME="bugfix/$(date +%Y-%m-%d)-$1"

cd "$REPO_PATH"

# 创建并切换到新分支
git checkout -b "$BRANCH_NAME"

echo "Created branch: $BRANCH_NAME"
echo "Edit files and run: git commit -am 'fix: description' && git push origin $BRANCH_NAME"
```

使用：
```bash
skill-fix.sh database-error
```

---

## 故障排查

### 推送被拒绝

```bash
# 先拉取远程变更
git pull origin dev

# 如果有冲突，解决后
git add .
git commit -m "resolve merge conflicts"

# 再推送
git push origin dev
```

### 符号链接失效

```bash
# 检查符号链接
ls -la /path/to/openclaw/skills/

# 如果是红色，说明目标不存在，删除重建
rm /path/to/openclaw/skills/status-benchmark-manage
ln -s /path/to/你的仓库名/.claude/skills/status-benchmark-manage \
      /path/to/openclaw/skills/status-benchmark-manage
```

### OpenClaw 未加载最新 skill

```bash
# 检查 git 是否拉取成功
cd /path/to/你的仓库名
git log -1

# 检查文件内容
cat .claude/skills/status-benchmark-manage/SKILL.md

# 重启 OpenClaw
systemctl restart openclaw
# 或根据你的系统
openclaw reload
```

---

## 下一步

- [ ] 配置 GitHub Actions 自动部署
- [ ] 设置服务器自动拉取 cron 任务
- [ ] 添加 pre-commit hooks 验证 skill 语法
- [ ] 设置 Issue 追踪和 PR 流程

---

**文档版本**: 1.0
**最后更新**: 2025-02-27
**维护者**: [你的名字]
