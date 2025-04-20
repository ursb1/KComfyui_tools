import subprocess

process = subprocess.Popen(
    ["./frpc", "-c", "./frpc.toml"],
    start_new_session=True
)