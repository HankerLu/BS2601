我想创建一个新skill，这个skill 负责维护我在周期阶段内的实时状态达标线（status benchmark），该skill会计算和同步实时状态达标线（status benchmark）的达成情况。
实时状态达标线（status benchmark）的具体定义：一个特定周期下的具体指标的及格线，比如，每天的工作时间占比>=50%，每周的娱乐时间总量<=10%，等等。
这个skill的具体功能如下：
1. 用户向skill 新增，删除或修改status benchmark
2. skill 掌握所有status benchmark的当前值的计算方式以及获取用于计算status benchmark的当前值的源信息的方式，比如，计算“每天的工作时间占比”需要从指定飞书多维表格链接获取每日工作时间，那么这个skill就会维护一个用于获取该status benchmark的当前值的脚本用于在被要求更新当前值时进行调用
3. skill 在被外界指定更新具体status benchmark的当前值是会自动调用相关工具或脚本获取源数据并计算该status benchmar的当前值并更新到数据表中。
目前有一些已经定好的status benchmark，可以先预装到skill中（注意，这些status benchmark 是未来可删改的，因此要注意存储方式）。如下：
1. 每日工作时间 >= 5小时
2. 每周工作时间 >= 35 小时
3. 每日创作时间 >= 4小时
4. 每周创作时间 >= 25 小时
5. 每日娱乐+放松时间 <= 1小时
6. 每日运动时间 >= 0.5小时
7. 每周运动时间 >= 5小时
原始数据来源：
donelist 飞书多维表格：https://my.feishu.cn/base/AUagbEJ3ZadyjwsfjAPcD991nGg?table=tblFXOx2aYXcDLLw&view=vewjPhzV7h
以上表格包含了我从2026年以来的time log，包含了工作，娱乐，生活-放松，等时间类别