import subprocess
import time
import re
import argparse
import sys
import shlex
import os # 需要 os 来支持 start_new_session

# --- 参数解析 ---
parser = argparse.ArgumentParser(description="启动 Pinggy SSH 隧道, 打印 URL 后退出")
parser.add_argument("--port", type=int, default=1145, help="要映射的本地端口号 (默认: 1145)")
parser.add_argument("--timeout", type=int, default=45, help="等待 URL 的超时时间 (秒)")
args, unknown = parser.parse_known_args()

# --- 配置 ---
LP = args.port
T_OUT = args.timeout
SVR, SP = "a.pinggy.io", 443
# 使用 shlex 安全分割命令
CMD = f"ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {SP} -R0:localhost:{shlex.quote(str(LP))} {SVR}"
proc = None

print(f"准备启动 SSH 隧道进程: localhost:{LP} -> {SVR}:{SP}...", flush=True)

try:
    # ★★★ 关键: 使用 start_new_session=True 尝试分离 SSH 进程 ★★★
    # 将 stdout 和 stderr 合并并通过管道读取
    proc = subprocess.Popen(
        shlex.split(CMD),
        stdout=subprocess.PIPE,    # 从管道读取 stdout
        stderr=subprocess.STDOUT, # 将 stderr 合并到 stdout
        text=True,                # 使用文本模式
        bufsize=1,                # 行缓冲
        universal_newlines=True,  # 确保跨平台文本模式一致性
        start_new_session=True    # <<< 让 SSH 进程在新的会话中启动
    )
    print(f"SSH 进程已启动 (PID: {proc.pid}). 正在监听输出来获取 URL ({T_OUT}s)...", flush=True)

except FileNotFoundError:
    print("\n❌ 错误: 'ssh' 命令未找到。请确保 SSH 客户端已安装。", flush=True, file=sys.stderr)
    sys.exit(1) # 脚本错误退出
except Exception as e:
    print(f"\n❌ 启动 SSH 时发生错误: {e}", flush=True, file=sys.stderr)
    sys.exit(1) # 脚本错误退出

# --- 监控 SSH 输出以捕获 URL ---
start_time = time.time()
url_found = False
url = None

try:
    for line in iter(proc.stdout.readline, ''):
        current_time = time.time()

        # (可选) 如果需要调试，可以取消下面这行的注释来查看原始 SSH 输出
        # print(f"  [SSH_DBG]: {line.strip()}", flush=True)

        # 检查是否包含 URL
        if match := re.search(r'(https?://[a-zA-Z0-9-]+\.pinggy\.link)', line):
            url = match.group(1)
            # ★★★ 打印找到的 URL (这是脚本的主要输出之一) ★★★
            print(f"\n✅✅✅ URL: {url} ✅✅✅\n", flush=True)
            url_found = True
            break # 找到 URL，跳出读取循环

        # 检查是否超时
        if current_time - start_time > T_OUT:
            print(f"\n⚠️ 等待 URL 超时 ({T_OUT}s)。脚本将退出。", flush=True, file=sys.stderr)
            break # 超时，跳出读取循环

        # 检查 SSH 进程是否在中途意外退出
        if not line and proc.poll() is not None:
             # readline 返回空字符串通常意味着 EOF 或进程结束
             print(f"\n❌ SSH 进程 (PID: {proc.pid}) 已意外终止。脚本将退出。", flush=True, file=sys.stderr)
             break

except Exception as e:
    print(f"\n❌ 读取 SSH 输出时发生错误: {e}", flush=True, file=sys.stderr)

# --- 脚本结束逻辑 ---
if url_found:
    print(f"URL 已找到并打印。此启动脚本现在将退出。", flush=True)
    print(f"SSH 隧道进程 (PID: {proc.pid}) 正在后台独立运行。", flush=True)
    # ★★★ 脚本正常退出 ★★★
    sys.exit(0)
else:
    # 如果是因为超时或错误退出循环
    print(f"未能成功获取 URL。此启动脚本退出。", flush=True, file=sys.stderr)
    # 尝试清理可能仍在运行但未成功的 SSH 进程
    if proc and proc.poll() is None:
        print(f"正在尝试终止未能提供 URL 的 SSH 进程 (PID: {proc.pid})...", flush=True)
        try:
            proc.terminate() # 发送 SIGTERM
            proc.wait(timeout=2) # 等待一段时间让其结束
        except subprocess.TimeoutExpired: # 如果没结束
            if proc.poll() is None:
                 proc.kill() # 发送 SIGKILL
        except Exception:
             # 忽略清理过程中的其他错误
             pass
    # ★★★ 脚本错误退出 ★★★
    sys.exit(1)
