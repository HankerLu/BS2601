# Skill 双向同步工作流文档

本文档描述如何在本地 Claude Code 和远程 OpenClaw 服务器之间实现 skill 的双向同步，包括本地开发迭代和服务器的自我优化。

## 架构设计

### 分支策略
```
main          # 稳定版本，本地和服务器共同维护
dev           # 本地 Claude Code 开发分支（不推送）
```

### 工作流程概览

**架构说明**：
- 本地 Mac：使用 Claude Code 主动开发编辑 skill
- 远程服务器：运行 OpenClaw，自我优化并修改 skill
- GitHub：代码仓库，作为两台电脑之间的中介
- 双向同步：服务器自我优化后自动提交，本地开发前拉取最新代码

```
┌─────────────────────┐         ┌──────────────┐         ┌──────────────────┐
│  本地电脑 (Mac)     │  Git    │   GitHub     │  Git    │  服务器 (Linux)  │
│  + Claude Code      │ <----> │  (代码仓库)   │ <----> │  + OpenClaw      │
│  (主动开发)         │         │              │         │  (自我优化+运行)  │
└─────────────────────┘         └──────────────┘         └──────────────────┘
      dev 分支                    main 分支              自动提交到 main
      ↓ merge to main                                      ↑
                                                          OpenClaw 修改后自动提交
                                                          (定时或触发式)

流程：
本地开发：
  1. 拉取最新代码（包含服务器的自我优化）
  2. 在 dev 分支开发
  3. 合并到 main 并推送

服务器优化：
  1. OpenClaw 运行并修改 skill
  2. 自动提交修改并推送到 GitHub
  3. 本地下次开发时拉取这些修改

冲突处理：
  1. 本地和服务器同时修改同一文件
  2. GitHub 检测到冲突
  3. 手动审查并解决冲突
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

# 创建 dev 分支（不推送到远程，dev 是本地开发分支）
git checkout -b dev
```

### 日常开发操作

```bash
# 1. 开发前同步最新代码（关键！）
git checkout dev

# 先拉取 main 的最新变更（包含服务器的自我优化）
git pull origin main

# 解决可能的冲突
# 如果有冲突，git 会提示你编辑文件，解决后：
git add .
git commit -m "resolve conflicts from server self-optimization"

# 2. 编辑 skill 文件（用 Claude Code）

# 3. 提交变更
git add .claude/skills/status-benchmark-manage/
git commit -m "feat: add new feature"

# 4. 合并到 main（可能再次产生冲突）
git checkout main

# 拉取最新代码（防止服务器又有了新修改）
git pull origin main

# 合并 dev 到 main
git merge dev

# 如果有冲突，解决后
git add .
git commit -m "merge dev with server changes"

# 5. 推送到 GitHub
git push origin main
```

### 开发前检查清单

- [ ] 切换到 dev 分支
- [ ] 拉取 main 最新代码（**最重要！包含服务器的自我优化**）
- [ ] 查看是否有来自服务器的变更
- [ ] 如果有冲突，先理解服务器的修改意图
- [ ] 在 dev 分支完成开发
- [ ] 合并到 main 时再次检查冲突
- [ ] 推送到 GitHub

### 查看服务器的自我优化修改

```bash
# 查看本地和远程的差异
git fetch origin
git log origin/main..HEAD  # 本地独有的提交
git log HEAD..origin/main  # 服务器独有的提交（自我优化）

# 查看具体差异
git diff origin/main

# 查看特定文件的服务器修改
git diff origin/main .claude/skills/status-benchmark-manage/SKILL.md
```

---

## 服务器（OpenClaw 环境）操作

### 初始化阶段（一次性）

```bash
# 1. SSH 登录服务器
ssh user@your-server

# 2. 克隆仓库到合适的位置
cd /path/to
git clone https://github.com/你的用户名/你的仓庛名.git

# 3. 创建 OpenClaw 的 skills 目录（如果不存在）
mkdir -p /path/to/openclaw/skills/

# 4. 建立符号链接
# 这样 OpenClaw 可以访问 skill 文件
# 同时 git 仓库也能看到修改
ln -s /path/to/你的仓庛名/.claude/skills/status-benchmark-manage \
      /path/to/openclaw/skills/status-benchmark-manage

ln -s /path/to/你的仓庛名/.claude/skills/target-benchmark-manage \
      /path/to/openclaw/skills/target-benchmark-manage

# 5. 配置 Git（如果还没有）
cd /path/to/你的仓庛名
git config user.name "OpenClaw Server"
git config user.email "openclaw@server"

# 6. 配置 GitHub 访问
# 生成 SSH 密钥
ssh-keygen -t rsa -b 4096 -C "openclaw-server" -f ~/.ssh/openclaw-server-key

# 将公钥添加到 GitHub 账户
cat ~/.ssh/openclaw-server-key.pub
# 复制内容到 GitHub → Settings → SSH and GPG keys

# 测试连接
ssh -T git@github.com

# 配置 git 使用 SSH
git remote set-url origin git@github.com:你的用户名/你的仓庛名.git
```

### 配置自动提交机制

#### 方案1：定时提交（推荐）

创建定时任务，定期检查并提交 OpenClaw 的修改：

```bash
# 创建自动提交脚本
cat > /usr/local/bin/auto-commit-skills.sh << 'EOF'
#!/bin/bash

REPO_PATH="/path/to/你的仓庛名"
LOG_FILE="/var/log/skill-auto-commit.log"

cd "$REPO_PATH" || exit 1

# 检查是否有修改
if [ -n "$(git status --porcelain)" ]; then
    echo "$(date): 发现修改，开始提交..." >> "$LOG_FILE"

    # 查看修改了哪些文件
    git status >> "$LOG_FILE"

    # 添加所有修改
    git add .

    # 提交
    git commit -m "auto: OpenClaw self-optimization at $(date '+%Y-%m-%d %H:%M:%S')"

    # 推送到 GitHub
    git push origin main

    if [ $? -eq 0 ]; then
        echo "$(date): 提交并推送成功" >> "$LOG_FILE"
    else
        echo "$(date): 推送失败" >> "$LOG_FILE"
    fi
else
    echo "$(date): 无修改，跳过" >> "$LOG_FILE"
fi
EOF

# 设置权限
chmod +x /usr/local/bin/auto-commit-skills.sh

# 添加到 crontab（每 10 分钟检查一次）
crontab -e

# 添加以下行：
*/10 * * * * /usr/local/bin/auto-commit-skills.sh >> /var/log/skill-auto-commit.log 2>&1
```

#### 方案2：修改后立即提交

创建一个 Git Hook，在文件修改时自动提交：

```bash
# 在服务器上
cd /path/to/你的仓庛名

# 创建 post-commit hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# 每次提交后自动推送到 GitHub
git push origin main
EOF

chmod +x .git/hooks/post-commit
```

但这个方案需要 OpenClaw 在修改文件后手动触发 git 提交。

#### 方案3：使用 inotify 实时监控

```bash
# 安装 inotify-tools
sudo apt-get install inotify-tools  # Debian/Ubuntu
# 或
sudo yum install inotify-tools      # CentOS/RHEL

# 创建监控脚本
cat > /usr/local/bin/watch-skills.sh << 'EOF'
#!/bin/bash

WATCH_DIR="/path/to/openclaw/skills"
REPO_PATH="/path/to/你的仓庛名"

while inotifywait -r -e modify,create,delete "$WATCH_DIR"; do
    sleep 5  # 等待 5 秒，确保文件修改完成

    cd "$REPO_PATH"
    if [ -n "$(git status --porcelain)" ]; then
        git add .
        git commit -m "auto: skill modification detected at $(date)"
        git push origin main
    fi
done
EOF

chmod +x /usr/local/bin/watch-skills.sh

# 后台运行
nohup /usr/local/bin/watch-skills.sh > /dev/null 2>&1 &
```

### 验证自动提交

```bash
# 查看日志
tail -f /var/log/skill-auto-commit.log

# 手动测试自动提交脚本
/usr/local/bin/auto-commit-skills.sh

# 查看提交历史
cd /path/to/你的仓庛名
git log --oneline -10
```

### 手动提交（紧急情况）

如果 OpenClaw 做了重要修改需要立即提交：

```bash
cd /path/to/你的仓庛名

# 查看修改
git status
git diff

# 提交
git add .
git commit -m "fix: emergency optimization"

# 推送
git push origin main
```

---

## 冲突处理

### 场景1：本地开发时发现服务器有新提交

```bash
# 在 dev 分支开发时
git checkout dev
git pull origin main

# 如果提示有冲突，先查看服务器的修改
git log HEAD..origin/main --oneline

# 查看具体差异
git diff origin/main .claude/skills/status-benchmark-manage/SKILL.md

# 如果服务器修改是自我优化，应该保留
# 手动合并，保留服务器的修改
git merge origin/main --no-ff

# 解决冲突后
git add .
git commit -m "merge: preserve server self-optimization"
```

### 场景2：服务器提交时发现本地有未推送的修改

```bash
# 在服务器上，自动提交脚本推送失败
# 因为本地有新的 push

# 解决方法：
# 1. 在本地重新拉取并合并
git pull origin main

# 2. 如果有冲突，解决后推送
git push origin main

# 3. 服务器下次定时任务就能正常推送
```

### 场景3：本地和服务器同时修改同一文件的同一行

```bash
# 在本地合并时
git checkout main
git pull origin main
git merge dev

# git 会标记冲突
# 编辑冲突文件，保留两个版本的意图
# 例如：
# <<<<<<< HEAD
# # 服务器添加的功能
# =======
# # 本地添加的功能
# >>>>>>> dev

# 合并为：
# # 服务器添加的功能
# # 本地添加的功能

git add .
git commit -m "resolve: merge server and local changes"
git push origin main
```

### 最佳实践

1. **开发前总是先拉取最新代码**
2. **查看服务器的修改，理解其意图**
3. **保留服务器的自我优化**
4. **冲突时优先考虑服务器修改**
5. **重要修改前通知正在使用 OpenClaw 的人**

---

## GitHub Actions 配置

由于服务器会自动推送，GitHub Actions 不再需要自动部署，改为**通知机制**：

### 创建通知工作流

在项目根目录创建 `.github/workflows/notify-changes.yml`：

```yaml
name: Notify on Server Push

on:
  push:
    branches:
      - main

jobs:
  notify:
    runs-on: ubuntu-latest
    if: github.event.pusher.name != '你的GitHub用户名'  # 排除自己的推送

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Get changed files
        id: changed-files
        uses: tj-actions/changed-files@v42
        with:
          files: |
            .claude/skills/**/*

      - name: Create notification issue
        if: steps.changed-files.outputs.any_changed == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const changedFiles = ${{ steps.changed-files.outputs.all_changed_files }};
            const issue = await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'OpenClaw self-optimization detected',
              body: `## Server Push Detected

              Pusher: ${{ github.event.pusher.name }}
              Time: ${{ github.event.head_commit.timestamp }}
              Commit: ${{ github.event.head_commit.message }}

              ### Changed Files:
              ${changedFiles.join('\n')}

              ### Action Required:
              Please review the changes before your next development session.`
            });
```

### 配置 GitHub Secrets

不需要配置 secrets，因为不需要 SSH 连接服务器了。

---

## 操作场景对照表

| 操作场景 | 本地 Claude Code | 服务器 OpenClaw |
|---------|----------------|-----------------|
| **初始化** | git init, git remote add, git push | git clone, 配置符号链接, 配置自动提交 |
| **正常开发** | 拉取最新代码 → 编辑 → 合并 → 推送 | 自动提交修改（定时或触发） |
| **新功能开发** | dev 分支开发 → merge 到 main | 不涉及 |
| **自我优化** | 不涉及 | 修改 skill → 自动提交推送 |
| **冲突处理** | 拉取服务器修改 → 手动合并 | 推送失败 → 等待本地处理 |
| **查看修改** | git log 查看服务器提交 | git log 查看本地提交 |

---

## 最佳实践

### Commit Message 规范

**本地开发**：
```bash
# 新功能
git commit -m "feat: add weight tracking feature"

# 修复问题
git commit -m "fix: correct database connection error"

# 文档更新
git commit -m "docs: update README with sync workflow"

# 合并服务器修改
git commit -m "merge: incorporate server self-optimization"

# 解决冲突
git commit -m "resolve: merge server optimization with local changes"
```

**服务器自动提交**（由脚本自动生成）：
```bash
git commit -m "auto: OpenClaw self-optimization at 2025-02-27 14:30:00"
```

### 本地开发检查清单

- [ ] 切换到 dev 分支
- [ ] **拉取 main 最新代码（包含服务器的自我优化）**
- [ ] 查看并理解服务器的修改
- [ ] 解决可能的冲突
- [ ] 在 dev 分支完成开发
- [ ] 合并到 main
- [ ] **再次拉取，确保服务器没有新提交**
- [ ] 解决可能的冲突
- [ ] 推送到 GitHub

### 服务器维护检查清单

- [ ] 检查自动提交日志
- [ ] 确认符号链接正常
- [ ] 验证 Git 配置
- [ ] 测试 SSH 连接 GitHub
- [ ] 定期查看提交历史

### 冲突预防

1. **本地开发前先拉取最新代码**
2. **查看服务器的自我优化日志**
3. **重要开发前通知相关人员**
4. **避免在服务器进行自我优化时本地开发**
5. **及时处理冲突，不要拖延**

---

## 快捷命令别名（可选）

### 本地 Git 别名

在 `~/.gitconfig` 中添加：

```ini
[alias]
    # 快速同步和推送
    dev-sync = "!f() { git checkout dev && git pull origin main; }; f"
    dev-push = "!f() { git add . && git commit -m \"$1\" && git checkout main && git pull origin main && git merge dev && git push origin main; }; f"
    show-server = "!f() { git fetch origin && git log HEAD..origin/main --oneline; }; f"
    show-local = "!f() { git fetch origin && git log origin/main..HEAD --oneline; }; f"

    # 快速查看分支
    branches = branch -a

    # 快速查看状态
    st = status
```

使用示例：
```bash
git dev-sync          # 同步 dev 分支并拉取服务器修改
git dev-push "add feature"  # 提交并合并到 main
git show-server       # 查看服务器的自我优化提交
git show-local        # 查看本地的开发提交
```

---

## 故障排查

### 推送被拒绝

```bash
# 原因：服务器有新的提交

# 解决方法：
git pull origin main

# 如果有冲突
git add .
git commit -m "resolve merge conflicts"

# 再推送
git push origin main
```

### 服务器自动提交失败

```bash
# 1. 查看日志
tail -f /var/log/skill-auto-commit.log

# 2. 手动测试
/usr/local/bin/auto-commit-skills.sh

# 3. 检查 Git 配置
cd /path/to/你的仓庛名
git config --list

# 4. 测试 GitHub 连接
ssh -T git@github.com

# 5. 如果是认证问题，重新配置 SSH 密钥
```

### 符号链接失效

```bash
# 检查符号链接
ls -la /path/to/openclaw/skills/

# 如果链接失效，删除重建
rm /path/to/openclaw/skills/status-benchmark-manage
ln -s /path/to/你的仓庛名/.claude/skills/status-benchmark-manage \
      /path/to/openclaw/skills/status-benchmark-manage
```

### 冲突难以解决

```bash
# 使用三路合并工具
git mergetool

# 或者保留某个版本
git checkout --ours file.txt  # 保留本地版本
git checkout --theirs file.txt  # 保留服务器版本

# 或者查看差异后手动编辑
git diff origin/main file.txt
```

### 无法合并服务器的自我优化

如果服务器的自我优化与本地开发严重冲突：

```bash
# 1. 创建备份分支
git branch backup-dev

# 2. 丢弃本地修改，采用服务器版本
git reset --hard origin/main

# 3. 重新开发
git checkout -b dev
# 重新进行开发

# 或者：手动逐个合并服务器的提交
git cherry-pick <commit-hash>
```

---

## 监控和追踪

### 查看服务器的自我优化历史

```bash
# 查看所有来自服务器的提交
git log --author="OpenClaw Server" --oneline

# 查看具体的自我优化内容
git show <commit-hash>

# 统计服务器的提交频率
git log --author="OpenClaw Server" --oneline | wc -l
```

### 设置邮件通知（可选）

在服务器上配置 Git 推送后的邮件通知：

```bash
# 安装 gitnotify
# 创建 post-push hook
cat > /path/to/你的仓庛名/.git/hooks/post-push << 'EOF'
#!/bin/bash
git log -1 --format="%H|%s|%an|%ae|%ai" | \
    while IFS='|' read hash msg author email date; do
        echo "Git push from server:
Commit: $hash
Message: $msg
Author: $author
Email: $email
Date: $date" | mail -s "OpenClaw Git Push Notification" your-email@example.com
    done
EOF

chmod +x /path/to/你的仓庛名/.git/hooks/post-push
```

---

## 下一步

- [x] 配置服务器自动提交机制
- [x] 配置 GitHub Actions 通知
- [ ] 添加 pre-commit hooks 验证 skill 语法
- [ ] 设置 Issue 追踪和 PR 流程
- [ ] 编写 skill 开发和自我优化文档
- [ ] 设置监控和告警

---

**文档版本**: 3.0
**最后更新**: 2025-02-27
**维护者**: [你的名字]
