1. target benchmark 定时汇报提醒及进度更新，以上午10:00为时间点，提醒用户汇报用于更新target benchmark的当前值的数据，若到14:00还没更新，则提醒用户汇报未更新的数据来源；
2. status benchmark 定时自动化计算和达标判定，以每日晚上23:00为自动化计算时间点，自动调用status benchmark manage 技能更新待更新的status benchmark，并向用户发送消息汇报；
3. 定期（每三天）向用户发送一份 汇总了 target benchmark 和 status benchmark 进展的简报