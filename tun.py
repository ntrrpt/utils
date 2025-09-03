#!/usr/bin/env python3
import asyncio
import signal
import sys
import time

REMOTE_USER = "root"
REMOTE_HOST = "123.456.0.789"
SSH_KEY = "/home/user/.ssh/id_rsa"
LOG_FILE = "/tmp/tun.log"

# tcp / udp proxies
# fmt:
# - TCP: "REMOTE:LOCAL"
# - UDP: {"udp": {"remote_port":X, "local_host":Y, "local_port":Z}}

SSH_TUNNELS = [
    # copyparty (local only, for reverse-proxies)
    {"type": "tcp", "remote_host": "localhost", "remote_port": 53923, "local_host": "localhost", "local_port": 3923},
    
    # ssh
    {"type": "tcp", "remote_host": "0.0.0.0", "remote_port": 44422, "local_host": "localhost", "local_port": 22},

    # UDP ports for port knocking
    {"type": "udp", "remote_port": 1234, "tcp_port": 51234, "local_host": "localhost", "local_port": 1234},
    {"type": "udp", "remote_port": 2345, "tcp_port": 52345, "local_host": "localhost", "local_port": 2345},
    {"type": "udp", "remote_port": 3456, "tcp_port": 53456, "local_host": "localhost", "local_port": 3456},
]

ssh_proc = None
local_socat_procs = []
running = True

def log(msg):
    s = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(f"{s}\n")
    print(msg)


def build_ssh_command():
    cmd = [
        "ssh", "-t",
        "-i", SSH_KEY,
        "-o", "ServerAliveInterval=60",
        "-o", "ServerAliveCountMax=3",
        "-o", "ConnectTimeout=10",
    ]

    # TCP and proxy for UDP (tcp_port)
    for t in SSH_TUNNELS:
        if t["type"] == "tcp":
            cmd.extend(
                [
                    "-R", f"{t['remote_host']}:{t['remote_port']}:{t['local_host']}:{t['local_port']}",
                ]
            )
        elif t["type"] == "udp":
            cmd.extend(["-R", f"{t['tcp_port']}:localhost:{t['tcp_port']}"])

    socat_cmds = []
    for t in SSH_TUNNELS:
        if t["type"] == "udp":
            socat_cmds.append(
                f"exec socat -T60 UDP4-LISTEN:{t['remote_port']},fork TCP:127.0.0.1:{t['tcp_port']}"
            )

    cmd.append(f"{REMOTE_USER}@{REMOTE_HOST}")

    if socat_cmds:
        remote_script = "set -e; " + " & ".join(socat_cmds) + "; wait"
        cmd.append(f'bash -c "{remote_script}"')
    else:
        cmd.append("-N")  # only TCP, -N untested with -t

    return cmd


async def start_ssh():
    cmd = build_ssh_command()
    log(f"[INFO] Starting SSH")# {' '.join(cmd)}")
    return await asyncio.create_subprocess_exec(*cmd)


async def start_local_socat(t):
    cmd = [
        "socat",
        f"TCP-LISTEN:{t['tcp_port']},fork",
        f"UDP:{t['local_host']}:{t['local_port']}",
    ]
    log(f"[INFO] Starting local socat: {' '.join(cmd)}")
    return await asyncio.create_subprocess_exec(*cmd)


async def monitor():
    global ssh_proc
    ssh_proc = await start_ssh()

    # statring local socat only for UDP
    udp_indexes = []  # (index in SSH_TUNNELS -> index in local_socat_procs)
    for idx, t in enumerate(SSH_TUNNELS):
        if t["type"] == "udp":
            proc = await start_local_socat(t)
            udp_indexes.append(len(local_socat_procs))  # idx in local_socat_procs
            local_socat_procs.append(proc)

    while running:
        # ssh check
        if ssh_proc.returncode is not None:
            log("[WARN] SSH disconnected, restarting...")
            ssh_proc = await start_ssh()

        # local socat check
        udp_proc_index = 0
        for idx, t in enumerate(SSH_TUNNELS):
            if t["type"] == "udp":
                proc = local_socat_procs[udp_proc_index]
                if proc.returncode is not None:
                    log(
                        f"[WARN] Local socat for {t['remote_port']} died, restarting..."
                    )
                    local_socat_procs[udp_proc_index] = await start_local_socat(t)
                udp_proc_index += 1

        await asyncio.sleep(3)


def cleanup():
    global running
    running = False
    log("[INFO] Cleaning up...")
    if ssh_proc:
        ssh_proc.terminate()
    for proc in local_socat_procs:
        proc.terminate()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, cleanup)
    try:
        loop.run_until_complete(monitor())
    finally:
        loop.close()
