import threading
import subprocess
import time
import re
import sys
import shlex # 用于更安全地分割命令

# --- 配置 ---
LOCAL_PORT_TO_EXPOSE = 1145 # 你想暴露的本地端口
LOG_FILE_FOR_SSH = f"pinggy_ssh_port_{LOCAL_PORT_TO_EXPOSE}.log" # SSH进程的日志文件
TIMEOUT_SECONDS = 45        # 等待URL的最长时间

# --- 后台任务函数 ---
def run_pinggy_in_background(port, log_file, timeout):
    """在后台线程中运行 SSH 隧道，获取并打印 URL"""
    global pinggy_url # 使用全局变量来存储URL，主线程也可访问（可选）
    pinggy_url = None

    svr, sp = "a.pinggy.io", 443
    # 使用 shlex.quote 防止潜在的注入问题，更安全
    cmd = f"ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {sp} -R0:localhost:{shlex.quote(str(port))} {svr}"
    proc = None

    print(f"[后台线程] 准备启动隧道: localhost:{port} -> {svr}:{sp}...", flush=True)
    print(f"[后台线程] SSH 输出将冗余记录到: {log_file}", flush=True)

    try:
        # 启动 SSH 进程，stdout/stderr 重定向到文件，也保留管道用于读取
        # 使用 Popen 启动后，此函数会监控并等待
        with open(log_file, "wb") as log_f: # 以二进制写入，避免编码问题
             proc = subprocess.Popen(shlex.split(cmd),
                                     stdout=subprocess.PIPE, # 保留管道用于实时读取
                                     stderr=subprocess.STDOUT, # 合并 stderr 到 stdout
                                     bufsize=1, # 行缓冲
                                     universal_newlines=True, # 按文本模式处理
                                     start_new_session=True) # 尝试让ssh更独立

             print(f"[后台线程] SSH 进程已启动 (PID: {proc.pid}). 实时监控输出获取 URL...", flush=True)

             start_time = time.time()
             url_found = False

             # 实时读取 SSH 输出流
             for line in iter(proc.stdout.readline, ''):
                 # 将读取到的行也写入日志文件
                 log_f.write(line.encode('utf-8', errors='ignore'))
                 log_f.flush()

                 # 检查是否超时
                 if time.time() - start_time > timeout:
                     if not url_found:
                         print(f"[后台线程] ⚠️ 等待 URL 超时 ({timeout}s)。", flush=True, file=sys.stderr)
                     break # 超时则停止读取

                 # 打印 SSH 输出（用于调试，如果不需要可以注释掉）
                 # print(f"  [SSH Output]: {line.strip()}", flush=True)

                 # 匹配 URL
                 if not url_found:
                     if match := re.search(r'(https?://[a-zA-Z0-9-]+\.pinggy\.link)', line):
                         pinggy_url = match.group(1)
                         print(f"\n[后台线程] ✅✅✅ 成功获取到 URL: {pinggy_url} ✅✅✅\n", flush=True)
                         url_found = True
                         # 找到URL后不退出循环，继续记录日志并等待进程结束

             # 如果循环结束（因为超时或进程结束）但仍未找到 URL
             if not url_found and proc.poll() is None:
                print(f"[后台线程] ⚠️ 监控结束前仍未找到 URL。SSH 进程 (PID: {proc.pid}) 可能仍在运行。", flush=True, file=sys.stderr)

             # 读取结束后，等待 SSH 进程终止
             if proc.poll() is None:
                print(f"[后台线程] URL捕获阶段完成。线程将继续等待 SSH 进程 (PID: {proc.pid}) 结束...", flush=True)
                proc.wait() # 等待进程结束
                print(f"[后台线程] SSH 进程 (PID: {proc.pid}) 已终止。", flush=True)
             else:
                print(f"[后台线程] SSH 进程 (PID: {proc.pid}) 在监控过程中已提前终止。退出码: {proc.returncode}", flush=True, file=sys.stderr)


    except FileNotFoundError:
         print("[后台线程] ❌ 错误: 'ssh' 命令未找到。请确保 SSH 客户端已安装。", flush=True, file=sys.stderr)
    except Exception as e:
         print(f"[后台线程] ❌ 在线程中发生错误: {e}", flush=True, file=sys.stderr)
    finally:
        print("[后台线程] 隧道管理线程执行完毕。", flush=True)

# --- 在 Notebook 单元格中运行 ---

print("准备在后台线程中启动 Pinggy 隧道...")

# 创建并启动后台线程
# daemon=True 使得主线程（Notebook内核）退出时，此线程也会强制结束（对于Notebook通常是期望行为）
pinggy_thread = threading.Thread(target=run_pinggy_in_background,
                                 args=(LOCAL_PORT_TO_EXPOSE, LOG_FILE_FOR_SSH, TIMEOUT_SECONDS),
                                 daemon=True)
pinggy_thread.start()

print(f"✅ 后台线程已启动。此单元格执行完毕，你可以运行其他单元格了。")
print(f"请留意上方的 '[后台线程]' 输出，它将在获取到 URL 时显示。")
print(f"详细 SSH 日志请查看文件: {LOG_FILE_FOR_SSH}")

# 这个单元格会立即结束执行
