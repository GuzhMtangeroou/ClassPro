import tkinter as tk
from tkinter import font

def run():
    # 创建主窗口
    root = tk.Tk()
    root.title("考试模式")

    # 设置窗口全屏
    root.attributes("-fullscreen", True)
    root.configure(bg="black")

    # 将窗口置于所有其他窗口之上
    root.attributes("-topmost", True)

    # 设置窗口不显示任务栏图标
    root.attributes("-toolwindow", True)

    # 创建字体
    custom_font = font.Font(family="Microsoft YaHei", size=25)

    # 创建标签并设置文字
    label = tk.Label(root, text="考试模式", font=custom_font, fg="white", bg="black")
    label.place(relx=0.5, rely=0.5, anchor="center")

    # 运行主循环
    root.mainloop()
#run()