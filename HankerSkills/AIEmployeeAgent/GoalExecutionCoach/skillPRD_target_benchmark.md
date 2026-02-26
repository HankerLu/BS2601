我想创建一个新skill，这个skill负责维护我的个人建立的长期量化目标（target benchmark），以及计算同步我完成目标的进度情况。
长期量化目标（target benchmark）的具体定义：定义了在一个具体的截止日期前到达到的某一个项目的指标，含具体的指标。比如，在2026年6月30日前体重达到75kg。
这个skill的具体功能如下：
1. 用户向skill 新增，删除或修改target benchmark
2. 用户可以向skill汇报某个target benchmark的当前数值
3. skill会在target benchmark的当前数值得到更新后，计算这个target benchmark的进度信息并同步到数据表中