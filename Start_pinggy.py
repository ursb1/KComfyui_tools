import subprocess
import shlex
import time

# --- 配置 ---
# 1. 你想要在 Kaggle 笔记本内部暴露的本地端口号
local_port = 8080

# 2. Pinggy 的 SSH 命令 (保持必要选项)
pinggy_command = f"ssh -p 443 -R0:localhost:{local_port} -o StrictHostKeyChecking=no -o ServerAliveInterval=60 a.pinggy.io"
# --- 配置结束 ---


# --- 执行 ---
# 1. 使用 shlex 安全地分割命令字符串
args = shlex.split(pinggy_command)

# 2. 使用 subprocess.Popen 启动 Pinggy 进程
#    省略 stdout 和 stderr 参数，让子进程继承父进程的输出流
#    这意味着 Pinggy 的输出会直接显示在下面的单元格输出中
print(f"正在尝试在后台启动 Pinggy...")
process = subprocess.Popen(args)

# 3. 打印提示信息
print(f"Pinggy 进程已启动 (PID: {process.pid}).")
print("请在下方（或上方，取决于输出缓冲）的单元格输出中查找 Pinggy 分配的 URL。")
print("等待几秒让连接信息输出...")

# 4. 短暂暂停，给 Pinggy 一点时间来连接并打印初始输出
#    这样用户更有可能在执行下一段代码前看到 URL
time.sleep(5) # 可以根据需要调整等待时间
