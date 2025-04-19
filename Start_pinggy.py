import pexpect
import sys
import re
import argparse

# 1. 参数解析
parser = argparse.ArgumentParser(description="简化版 Pinggy 启动器 (pexpect)")
parser.add_argument("--port", type=int, required=True, help="本地端口")
parser.add_argument("--timeout", type=int, default=90, help="等待 URL 超时秒数 (建议足够长)")
args = parser.parse_args()

# 2. 配置 SSH 命令和正则
CMD = f"ssh -p 443 -R0:localhost:{args.port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -T a.pinggy.io"
URL_REGEX = r'(https?://[a-zA-Z0-9-]+\.pinggy\.link)' # 用于匹配 Pinggy URL 的正则表达式

print(f"尝试使用 pexpect 启动 Pinggy (端口: {args.port}, 超时: {args.timeout}s)...", flush=True)

# 3. 使用 pexpect 启动并等待 URL
try:
    # 启动子进程
    child = pexpect.spawn(CMD, timeout=args.timeout, encoding='utf-8')

    # (可选) 将子进程的输出实时打印到Notebook的输出，方便调试
    # child.logfile_read = sys.stdout

    # 等待匹配 URL、进程结束(EOF) 或超时
    index = child.expect([URL_REGEX, pexpect.EOF, pexpect.TIMEOUT])

    if index == 0: # 成功匹配到 URL
        url = child.match.group(1)
        print(f"\n✅ 成功获取 URL: {url}\n", flush=True)
        # 关闭 pexpect 对子进程的控制连接，force=False 尝试不发送 SIGHUP 信号
        # 让后台的 SSH 进程继续运行（如果 Kaggle 环境允许）
        child.close(force=False)
        print("启动脚本完成，SSH 隧道应在后台运行。", flush=True)
        sys.exit(0) # 脚本正常退出
    else:
        # 情况: 进程在打印 URL 前就结束了 (EOF) 或超时 (TIMEOUT)
        print("错误：未能获取 Pinggy URL (可能超时或SSH进程提前退出)。", file=sys.stderr, flush=True)
        # 打印在出错/超时前捕获到的输出，帮助诊断
        print("--- SSH进程的部分输出 ---", file=sys.stderr)
        print(child.before, file=sys.stderr) # 打印匹配前的缓冲区内容
        print("--- 输出结束 ---", file=sys.stderr)
        sys.exit(1) # 脚本错误退出

except Exception as e:
    # 捕获 pexpect 可能抛出的其他异常
    print(f"运行 pexpect 时发生错误: {e}", file=sys.stderr, flush=True)
    sys.exit(1) # 脚本错误退出
