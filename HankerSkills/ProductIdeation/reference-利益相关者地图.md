利益相关者地图参考示例1:
digraph PostSurgeryRehabilitation {
    // --- 全局设置 ---
    graph [
        rankdir="LR",           // 设置布局方向为从左到右 (Left to Right)
        label="关节术后康复流程", // 图表标题
        labelloc="t",           // 标题位置在顶部
        fontsize=20,
        fontname="SimHei",      // 使用支持中文的字体，如黑体
        fontcolor="#d9534f"     // 标题颜色
    ];
    
    node [
        shape="box",            // 节点形状为方框
        style="filled,rounded", // 样式为填充、圆角
        fillcolor="#e6f0ff",    // 节点填充色 (淡蓝色)
        fontname="SimHei",      // 节点字体
        color="#b3cfff"         // 节点边框色
    ];
    
    edge [
        color="#808080",        // 箭头颜色为灰色
        fontname="SimHei"
    ];

    // --- 定义三个角色的"泳道" ---

    subgraph cluster_patient {
        label = "关节术后康复者";
        style = "filled";
        fillcolor = "#f8f9fa"; // 泳道背景色
        
        P1 [label="选择合适的泳道/泳池"];
        P2 [label="初次下水试验"];
        P3 [label="执行游泳方案"];
        P4 [label="定期复查"];
        P5 [label="恢复关节活动情况"];
    }

    subgraph cluster_doctor {
        label = "骨科医生";
        style = "filled";
        fillcolor = "#f8f9fa";

        D1 [label="评估术后情况"];
        D2 [label="开康复处方"];
        D3 [label="转介康复科"];
    }

    subgraph cluster_therapist {
        label = "康复治疗师";
        style = "filled";
        fillcolor = "#f8f9fa";

        T1 [label="评估患者运动能力"];
        T2 [label="制定游泳方案"];
        T3 [label="监测/记录数据"];
        T4 [label="动态调整"];
    }

    // --- 定义流程箭头 ---

    // 内部流程
    P1 -> P2 -> P3 -> P4 -> P5;
    D1 -> D2 -> D3;
    T1 -> T2 -> T3 -> T4;

    // 跨角色交互流程
    D3 -> T1 [label="转介"];
    T2 -> P3 [label="提供方案"];
    P4 -> T4 [label="反馈情况"];
    
    // 反馈循环
    T4 -> T1 [style=dashed, constraint=false, label="优化调整"]; // constraint=false 避免影响主布局
}

利益相关者地图参考示例2:
digraph FatLossSwimming {
    // --- 全局设置 ---
    graph [
        rankdir="LR",
        label="运动受限的减脂人群",
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

    // --- 定义三个角色的"泳道" ---

    subgraph cluster_user {
        label = "运动受限的减脂人群";
        style = "filled";
        fillcolor = "#f8f9fa";
        
        U1 [label="明确游泳目标\n2km, 开始游泳"];
        U2 [label="感到枯燥, 暂停游泳歇息,\n查看运动手表参数"];
        U3 [label="继续游泳一段距离, 体力不支,\n暂停游泳, 查看参数"];
        U4 [label="游完剩下的距离"];
        U5 [label="查看参数\n能量补给"];
        U6 [label="完成游泳目标,\n测算能量消耗"];
    }

    subgraph cluster_partner {
        label = "泳伴";
        style = "filled";
        fillcolor = "#f8f9fa";

        P1 [label="游泳陪伴"];
        P2 [label="提供鼓励"];
    }

    subgraph cluster_coach {
        label = "健身教练";
        style = "filled";
        fillcolor = "#f8f9fa";

        C1 [label="评估身体状况\n和减脂目标"];
        C2 [label="提供训练计划"];
    }

    // --- 定义流程箭头 ---

    // 内部流程
    U1 -> U2 -> U3 -> U4 -> U5 -> U6;
    P1 -> P2;
    C1 -> C2;

    // 跨角色交互流程
    P2 -> U2; // 泳伴的鼓励在用户感到枯燥时介入
    C1 -> U1; // 教练的评估帮助用户明确目标
    C2 -> U2; // 训练计划在用户感到枯燥/疲劳时作为参考
    
    // 反馈循环 (用户的数据提供给教练)
    U5 -> C1 [label="数据提供", style=dashed, constraint=false];
}

你是一位非常资深和有用户洞察力的产品经理，请你结合我的项目背景和价值主张，以及利益相关者地图的参考示例，绘制出结合我的项目背景和价值主张的利益相关者地图。

注意：
你要交付的利益相关者地图是产品未介入的利益相关者地图，而不是产品介入后的利益相关者地图。