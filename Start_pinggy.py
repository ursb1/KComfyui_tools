%%writefile start_pinggy.py
import subprocess
import time
import re
import argparse
import sys
import shlex
import os

# --- 参数解析 ---
parser = argparse.ArgumentParser(description="启动 Pinggy SSH 隧道并在获取 URL 后退出")
parser.add_argument("--port", type=int, required=True, help="要映射的本地端口号")
parser.add_argument("--timeout", type=int, default=30, help="等待 URL 的超时时间 (秒)")
args = parser.parse_args()

# --- 配置 ---
LOCAL_PORT = args.port
TIMEOUT = args.timeout
PINGGY_SERVER = "a.pinggy.io"
PINGGY_PORT = 443
SSH_COMMAND = f"ssh -p {PINGGY_PORT} -R0:localhost:{shlex.quote(str(LOCAL_PORT))} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -T {PINGGY_SERVER}"

# --- 启动进程 ---
proc = None
try:
    # 使用 start_new_session=True 尝试让 SSH 进程在后台独立运行
    proc = subprocess.Popen(
        shlex.split(SSH_COMMAND),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # 合并 stdout 和 stderr
        text=True,
        bufsize=1, # 行缓冲
        universal_newlines=True,
        start_new_session=True # 关键：尝试让进程独立
    )
    print(f"Pinggy process启动 (PID: {proc.pid}). 等待 URL ({TIMEOUT}s)...", flush=True)

except Exception as e:
    print(f"启动 SSH 失败: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

# --- 监控输出以获取 URL ---
start_time = time.time()
url_found = False
url = None

try:
    for line in iter(proc.stdout.readline, ''):
        # 调试时可取消注释下一行查看 SSH 输出
        # print(f"  [DBG]: {line.strip()}", flush=True)

        if match := re.search(r'(https?://[a-zA-Z0-9-]+\.pinggy\.link)', line):
            url = match.group(1)
            print(f"\n✅ Pinggy URL: {url}\n", flush=True) # 主要输出
            url_found = True
            break # 找到 URL，退出循环

        if time.time() - start_time > TIMEOUT:
            print(f"等待 URL 超时 ({TIMEOUT}秒).", file=sys.stderr, flush=True)
            break # 超时退出

        # 简单检查进程是否提前退出
        if proc.poll() is not None:
             print(f"SSH 进程 (PID: {proc.pid}) 意外终止.", file=sys.stderr, flush=True)
             break

except Exception as e:
    print(f"读取 SSH 输出时出错: {e}", file=sys.stderr, flush=True)

# --- 退出脚本 ---
if url_found:
    print(f"URL 已捕获。启动脚本 (不是 SSH 进程) 现在将退出。", flush=True)
    # 注意：这里我们**不**终止proc，依赖start_new_session使其后台运行
    sys.exit(0) # 成功退出
else:
    print(f"未能获取 Pinggy URL。启动脚本退出。", file=sys.stderr, flush=True)
    # 尝试清理失败的进程
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=1)
        except Exception:
            if proc.poll() is None: proc.kill() # 强制杀死
    sys.exit(1) # 失败退出
