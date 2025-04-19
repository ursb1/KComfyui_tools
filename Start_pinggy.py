import subprocess, time, re
import argparse # 导入 argparse

# --- 参数解析 ---
parser = argparse.ArgumentParser(description="启动 Pinggy SSH 隧道")
parser.add_argument("--port", type=int, default=1145, help="要映射的本地端口号 (默认: 1145)")
# 使用 parse_known_args() 忽略 Jupyter/Colab 传入的未知参数
args, unknown = parser.parse_known_args()
# --- 参数解析结束 ---

# --- 配置 ---
LP = args.port # 使用命令行传入或默认的端口
SVR, SP, T_OUT = "a.pinggy.io", 443, 45 # SSH服务器, SSH端口, 超时秒数
CMD = f"ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {SP} -R0:localhost:{LP} {SVR}"
# --- 配置结束 ---

print(f"启动隧道: localhost:{LP} -> {SVR}:{SP}...")
# 使用 shlex.split 更安全地处理命令拆分
proc = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
print(f"PID: {proc.pid}. 等待 URL ({T_OUT}s)...")

start = time.time()
url_found = False
try:
    for line in iter(proc.stdout.readline, ''):
        # 检查进程是否已结束
        if not line and proc.poll() is not None:
            print("\n❌ SSH 进程意外退出。")
            break
        # 超时检查
        if time.time() - start > T_OUT:
            print(f"\n⚠️ 超时 ({T_OUT}s). 未找到 URL。")
            break
        # 打印一些日志方便调试 (可注释掉)
        # print(f"  [SSH]: {line.strip()}")
        # 匹配URL
        if match := re.search(r'(https?://\S+\.pinggy\.link)', line):
            print(f"\n✅ URL: {match.group(1)}")
            url_found = True
            break # 找到URL就退出循环
finally:
    # 报告最终状态
    if url_found:
        print("隧道已建立并在后台运行。")
    elif proc.poll() is None:
        print("未捕获到URL，但 SSH 进程仍在后台运行。")
    else:
        print("SSH 进程已结束，且未捕获到URL。")

# 脚本执行到此结束，但SSH进程（如果仍在运行）会继续在后台工作