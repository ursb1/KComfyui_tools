import subprocess

process1 = subprocess.Popen(
    ["./res/frpc", "-c", "./res/frpc1145.ini"],
    stdout=subprocess.DEVNULL,  # 将标准输出重定向到 DEVNULL防止显示
    stderr=subprocess.DEVNULL,  # 将标准错误重定向到 DEVNULL
    start_new_session=True
)
process2 = subprocess.Popen(
    ["./res/frpc", "-c", "./res/frpc8080.ini"],
    stdout=subprocess.DEVNULL,  # 将标准输出重定向到 DEVNULL防止显示
    stderr=subprocess.DEVNULL,  # 将标准错误重定向到 DEVNULL
    start_new_session=True
)
print("访问1145端口：http://hk-6.lcf.im:51145")
print("访问8080端口：http://hk-6.lcf.im:58080")
print("进程管理：process1-1145，process2-8080")