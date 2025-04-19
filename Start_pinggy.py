import subprocess
import time
import re
import argparse
import sys

parser = argparse.ArgumentParser(description="启动 Pinggy SSH 隧道")
parser.add_argument("--port", type=int, default=1145, help="要映射的本地端口号 (默认: 1145)")
args, unknown = parser.parse_known_args()

LP = args.port
SVR, SP, T_OUT = "a.pinggy.io", 443, 45
CMD = f"ssh -T -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {SP} -R0:localhost:{LP} {SVR}"

print(f"启动隧道: localhost:{LP} -> {SVR}:{SP}...")
proc = None
try:
    proc = subprocess.Popen(CMD.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
except FileNotFoundError:
    print("\n❌ 错误: 'ssh' 命令未找到。请确保 SSH 客户端已安装并且在系统 PATH 中。")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ 启动 SSH 时发生错误: {e}")
    sys.exit(1)

print(f"PID: {proc.pid}. 等待 URL ({T_OUT}s)...")

start = time.time()
url_found = False
url = None

try:
    for line in iter(proc.stdout.readline, ''):
        if not line and proc.poll() is not None:
            print("\n❌ SSH 进程意外退出。")
            break
        if time.time() - start > T_OUT:
            print(f"\n⚠️ 超时 ({T_OUT}s). 未找到 URL。")
            break

        print(f"  [SSH]: {line.strip()}") # Keep this for debugging if needed

        if match := re.search(r'(https?://[a-zA-Z0-9-]+\.pinggy\.link)', line):
            url = match.group(1)
            print(f"\n✅ URL: {url}")
            url_found = True
            break

except Exception as e:
     print(f"\n❌ 读取 SSH 输出时出错: {e}")

finally:
    if url_found:
        print(f"隧道已建立 ({url}). 进程将在后台保持运行。")
        print(f"要停止隧道，请终止 PID: {proc.pid}")
        try:
             while proc.poll() is None:
                 time.sleep(10)
             print(f"\n⚠️ SSH 进程 (PID: {proc.pid}) 已终止。")
        except KeyboardInterrupt:
             print("\n用户中断，正在尝试终止 SSH 进程...")
             if proc and proc.poll() is None:
                 proc.terminate()
                 try:
                     proc.wait(timeout=5)
                 except subprocess.TimeoutExpired:
                     if proc.poll() is None:
                        proc.kill()
             print("脚本结束。")
        except Exception as e:
             print(f"\n❌ 等待 SSH 进程时出错: {e}")
    elif proc and proc.poll() is None:
        print("未捕获到 URL 或超时，但 SSH 进程仍在运行。请检查 SSH 输出。")
        print(f"要停止隧道，请终止 PID: {proc.pid}")
        # Keep script alive even if URL not found but process is running
        try:
             while proc.poll() is None:
                 time.sleep(10)
             print(f"\n⚠️ SSH 进程 (PID: {proc.pid}) 已终止。")
        except KeyboardInterrupt:
             print("\n用户中断，正在尝试终止 SSH 进程...")
             if proc and proc.poll() is None:
                  proc.terminate()
                  try:
                      proc.wait(timeout=5)
                  except subprocess.TimeoutExpired:
                      if proc.poll() is None:
                         proc.kill()
             print("脚本结束。")
        except Exception as e:
             print(f"\n❌ 等待 SSH 进程时出错: {e}")
    else:
        print("检查发现 SSH 进程已结束，且未捕获到 URL。")
        # Attempt to read remaining output for clues
        if proc:
            try:
                remaining_output, _ = proc.communicate(timeout=1)
                if remaining_output:
                    print("\nSSH 进程退出前的最后输出:")
                    print(remaining_output)
                print(f"SSH 进程退出代码: {proc.returncode}")
            except Exception as e:
                print(f"读取 SSH 剩余输出时出错: {e}")
