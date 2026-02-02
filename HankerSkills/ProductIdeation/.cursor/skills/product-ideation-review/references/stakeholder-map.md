# 利益相关者地图

## 概述

利益相关者地图（Stakeholder Map）是一种可视化工具，用于展示产品生态系统中所有相关角色及其交互关系。

**重要原则**: 绘制**产品未介入**的原始场景，而非产品介入后的理想状态。这有助于识别真实痛点和介入机会。

## 绘制方法

### 使用Graphviz DOT语言

我们使用Graphviz的DOT语言绘制泳道图（Swimlane Diagram），清晰展示不同角色的行为流程和交互。

### 基本结构

```dot
digraph StakeholderMap {
    // 全局设置
    graph [rankdir="LR", label="场景标题", labelloc="t"];
    node [shape="box", style="filled,rounded"];
    edge [color="#808080"];
    
    // 角色1的泳道
    subgraph cluster_role1 {
        label = "角色名称";
        A1 [label="行为/步骤1"];
        A2 [label="行为/步骤2"];
    }
    
    // 角色间交互
    A1 -> B1 [label="交互说明"];
}
```

## 完整案例1: 关节术后康复场景

### 场景描述
关节术后患者需要进行康复训练，涉及骨科医生、康复治疗师和患者本人的协作。

### 利益相关者地图

```dot
digraph PostSurgeryRehabilitation {
    // --- 全局设置 ---
    graph [
        rankdir="LR",           // 从左到右布局
        label="关节术后康复流程",
        labelloc="t",
        fontsize=20,
        fontname="SimHei",
        fontcolor="#d9534f"
    ];
    
    node [
        shape="box",
        style="filled,rounded",
        fillcolor="#e6f0ff",
        fontname="SimHei",
        color="#b3cfff"
    ];
    
    edge [
        color="#808080",
        fontname="SimHei"
    ];

    // --- 患者泳道 ---
    subgraph cluster_patient {
        label = "关节术后康复者";
        style = "filled";
        fillcolor = "#f8f9fa";
        
        P1 [label="选择合适的泳道/泳池"];
        P2 [label="初次下水试验"];
        P3 [label="执行游泳方案"];
        P4 [label="定期复查"];
        P5 [label="评估关节活动情况"];
    }

    // --- 骨科医生泳道 ---
    subgraph cluster_doctor {
        label = "骨科医生";
        style = "filled";
        fillcolor = "#f8f9fa";

        D1 [label="评估术后情况"];
        D2 [label="开具康复处方"];
        D3 [label="转介康复科"];
    }

    // --- 康复治疗师泳道 ---
    subgraph cluster_therapist {
        label = "康复治疗师";
        style = "filled";
        fillcolor = "#f8f9fa";

        T1 [label="评估患者运动能力"];
        T2 [label="制定游泳方案"];
        T3 [label="监测/记录数据"];
        T4 [label="动态调整方案"];
    }

    // --- 流程箭头 ---
    // 内部流程
    P1 -> P2 -> P3 -> P4 -> P5;
    D1 -> D2 -> D3;
    T1 -> T2 -> T3 -> T4;

    // 跨角色交互
    D3 -> T1 [label="转介"];
    T2 -> P3 [label="提供方案"];
    P4 -> T4 [label="反馈情况"];
    
    // 反馈循环
    T4 -> T1 [style=dashed, constraint=false, label="优化调整"];
}
```

### 关键洞察
1. **断点**: 患者从医生处获得处方后，到康复治疗师处执行之间存在信息传递断点
2. **痛点**: 康复治疗师无法实时监测患者在泳池中的执行情况
3. **机会**: 数据记录和反馈循环主要依赖患者自述，缺乏客观测量

## 完整案例2: 运动受限减脂人群游泳场景

### 场景描述
运动受限的肥胖人群希望通过游泳减脂，但常因疲劳、枯燥等原因难以坚持。

### 利益相关者地图

```dot
digraph FatLossSwimming {
    // --- 全局设置 ---
    graph [
        rankdir="LR",
        label="运动受限减脂人群游泳场景",
        labelloc="t",
        fontsize=20,
        fontname="SimHei",
        fontcolor="#d9534f"
    ];
    
    node [
        shape="box",
        style="filled,rounded",
        fillcolor="#e6f0ff",
        fontname="SimHei",
        color="#b3cfff"
    ];
    
    edge [
        color="#808080",
        fontname="SimHei"
    ];

    // --- 用户泳道 ---
    subgraph cluster_user {
        label = "运动受限的减脂人群";
        style = "filled";
        fillcolor = "#f8f9fa";
        
        U1 [label="设定目标\n(如2km)，开始游泳"];
        U2 [label="感到枯燥，暂停歇息\n查看运动手表参数"];
        U3 [label="继续游泳，体力不支\n再次暂停，查看参数"];
        U4 [label="游完剩余距离"];
        U5 [label="查看运动数据\n能量补给"];
        U6 [label="完成目标\n计算能量消耗"];
    }

    // --- 泳伴泳道 ---
    subgraph cluster_partner {
        label = "泳伴";
        style = "filled";
        fillcolor = "#f8f9fa";

        P1 [label="陪同游泳"];
        P2 [label="提供鼓励和支持"];
    }

    // --- 健身教练泳道 ---
    subgraph cluster_coach {
        label = "健身教练";
        style = "filled";
        fillcolor = "#f8f9fa";

        C1 [label="评估身体状况\n和减脂目标"];
        C2 [label="提供训练计划"];
    }

    // --- 流程箭头 ---
    // 内部流程
    U1 -> U2 -> U3 -> U4 -> U5 -> U6;
    P1 -> P2;
    C1 -> C2;

    // 跨角色交互
    P2 -> U2 [label="鼓励"];
    C1 -> U1 [label="指导"];
    C2 -> U2 [label="参考"];
    
    // 反馈循环
    U5 -> C1 [label="数据反馈", style=dashed, constraint=false];
}
```

### 关键洞察
1. **痛点**: 用户多次因疲劳/枯燥暂停，说明持续性是核心问题
2. **断点**: 教练的训练计划在执行过程中缺乏实时指导
3. **依赖**: 泳伴的鼓励是重要支持，但不总是可得
4. **机会**: 
   - 用户频繁查看参数，说明需要即时反馈
   - 数据反馈给教练是滞后的，缺乏实时调整机制

## 绘制步骤

### Step 1: 识别角色
列出所有与场景相关的角色：
- **主角色**: 直接使用产品/服务的核心用户
- **次要角色**: 影响决策或体验的其他利益相关者
- **外围角色**: 间接相关的角色

### Step 2: 映射行为流程
为每个角色列出典型行为序列：
- 使用动词+名词描述（如"查看参数"，"提供方案"）
- 标注决策点（选择、判断）
- 标注情感变化（枯燥、疲劳、满足）

### Step 3: 识别交互点
找出角色之间的交互：
- **信息流**: 谁向谁传递什么信息？
- **物品流**: 是否涉及物品交换？
- **情感流**: 是否有情感支持或影响？

### Step 4: 标注反馈循环
识别闭环流程：
- 数据收集 → 分析 → 调整 → 再收集
- 使用虚线箭头表示反馈

### Step 5: 可视化生成
使用Graphviz生成图表：

```bash
# 保存DOT代码到文件
cat > stakeholder_map.dot << 'EOF'
digraph {
    // 你的DOT代码
}
EOF

# 生成PNG图片
dot -Tpng stakeholder_map.dot -o stakeholder_map.png

# 生成SVG（推荐，矢量图）
dot -Tsvg stakeholder_map.dot -o stakeholder_map.svg
```

## 图表元素说明

### 节点样式
```dot
// 普通步骤
node [shape="box", style="filled,rounded", fillcolor="#e6f0ff"];

// 决策点（可选）
node [shape="diamond", fillcolor="#fff4e6"];

// 关键节点（可选）
node [style="filled,rounded,bold", fillcolor="#ffe6e6"];
```

### 连线样式
```dot
// 普通流程
A -> B;

// 反馈循环
A -> B [style=dashed, label="反馈"];

// 条件分支
A -> B [label="条件满足"];

// 避免影响布局
A -> B [constraint=false];
```

### 泳道样式
```dot
subgraph cluster_name {
    label = "角色名称";
    style = "filled";
    fillcolor = "#f8f9fa";  // 浅灰色背景
    
    // 该角色的所有节点
}
```

## 分析要点

### 1. 识别痛点
- **频繁暂停**: 表明流程中断问题
- **重复操作**: 可能存在效率提升机会
- **缺少连接**: 角色之间缺乏必要交互

### 2. 发现机会
- **信息断点**: 在哪里信息传递不畅？
- **等待时间**: 哪些步骤之间有时间间隔？
- **依赖缺失**: 哪些重要角色缺席或参与不足？

### 3. 验证假设
- 是否所有关键角色都已识别？
- 流程是否反映真实情况（而非理想状态）？
- 是否标注了关键决策点和情感变化？

## 常见错误

### ❌ 错误1: 画产品介入后的场景
```
错误示例：用户 -> 使用我们的App -> 完成训练
```
应该画：用户现在如何完成训练？遇到什么问题？

### ❌ 错误2: 只画主角色
很多产品的价值在于连接多个角色，忽略次要角色会遗漏重要洞察。

### ❌ 错误3: 流程过于简化
```
错误示例：用户 -> 游泳 -> 结束
```
应该细化：中间的暂停、查看数据、情绪变化等关键节点。

### ❌ 错误4: 缺少反馈循环
真实场景中往往有反复和迭代，一定要标注出来。

## 工具使用

### 在线Graphviz编辑器
- https://dreampuf.github.io/GraphvizOnline/
- https://edotor.net/

### 本地安装Graphviz
```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# Windows
# 下载安装包: https://graphviz.org/download/
```

### 集成到报告
生成的PNG或SVG可以直接嵌入HTML报告：
```html
<img src="stakeholder_map.png" alt="利益相关者地图" style="max-width: 100%;">
```

## 检查清单

完成利益相关者地图后，检查：
- [ ] 是否画的是产品未介入的原始场景？
- [ ] 是否包含所有关键角色（主要和次要）？
- [ ] 每个角色是否有清晰的行为流程？
- [ ] 是否标注了角色间的关键交互？
- [ ] 是否识别了反馈循环？
- [ ] 是否标注了痛点和断点？
- [ ] 图表是否清晰易读（不过于复杂）？
