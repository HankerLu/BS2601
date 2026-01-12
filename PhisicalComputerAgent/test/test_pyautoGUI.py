import pyautogui

# macOS 下通常建议设置个小的停顿，防止操作过快
pyautogui.PAUSE = 0.1 

# 获取屏幕宽高
screenWidth, screenHeight = pyautogui.size()

# 设置目标坐标 (例如屏幕中心)
x, y = screenWidth / 2, screenHeight / 2

# 移动鼠标
pyautogui.moveTo(x, y)

# 点击
pyautogui.click()

# 输入文字
pyautogui.write('hello world')
