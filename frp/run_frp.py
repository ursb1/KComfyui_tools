import subprocess

process = subprocess.Popen(
    ["./res/frpc", "-c", "./res/frpc.ini"],
    stdout=subprocess.DEVNULL,  # 将标准输出重定向到 DEVNULL防止显示
    stderr=subprocess.DEVNULL,  # 将标准错误重定向到 DEVNULL
    start_new_session=True
)
print("访问1145端口：sj.frp.one:51145")
print("访问8080端口：sj.frp.one:58080")