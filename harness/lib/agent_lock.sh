#!/usr/bin/env sh
# 轻量咨询式写锁：同一项目、同一时刻只允许一个 agent 写入，防多 agent 交叉污染。
#
# 用法:
#   agent_lock.sh acquire <agent> [project_dir] [--force]
#   agent_lock.sh release <agent> [project_dir] [--force]
#   agent_lock.sh status  [project_dir]
#
# 约定:
#   - 锁文件 <project>/.bio_harness/.lock，属运行态、不入库、不当共享证据。
#   - 咨询式：只对自觉先 acquire 的 agent 有效。强制接入 proof.py / gate 的锁检查是后续项。
#   - 陈旧阈值默认 30 分钟（BIO_LOCK_TTL 秒可调）；长写入应周期性重新 acquire 刷新时间戳。
#   - bash 3.x / POSIX sh 兼容：不用 declare -A、不用 bash4 特性。
#   - 所有面向用户的变量一律 ${} 花括号，避免紧贴中文标点时被并入变量名。
set -eu

TTL="${BIO_LOCK_TTL:-1800}"

usage() {
  echo "用法: agent_lock.sh acquire <agent> [project] [--force]" >&2
  echo "      agent_lock.sh release <agent> [project] [--force]" >&2
  echo "      agent_lock.sh status  [project]" >&2
  exit 2
}

cmd="${1:-}"
[ -n "${cmd}" ] || usage
shift || true

FORCE=0; P1=""; P2=""; n=0
for a in "$@"; do
  case "${a}" in
    --force) FORCE=1 ;;
    *) n=$((n + 1)); [ "${n}" = 1 ] && P1="${a}"; [ "${n}" = 2 ] && P2="${a}" ;;
  esac
done

case "${cmd}" in
  status) agent=""; proj="${P1:-.}" ;;
  acquire|release) agent="${P1:-}"; proj="${P2:-.}"; [ -n "${agent}" ] || usage ;;
  *) usage ;;
esac

projroot=$(cd "${proj}" 2>/dev/null && pwd) || { echo "项目目录不存在: ${proj}" >&2; exit 2; }
lockdir="${projroot}/.bio_harness"
lock="${lockdir}/.lock"

read_field() { # $1=key  -> 打印值（无锁则返回非零）
  [ -f "${lock}" ] || return 1
  sed -n "s/^$1=//p" "${lock}" 2>/dev/null | head -1
}

is_stale() { # 仅按 TTL 判定（acquire/release 是独立进程，pid 存活不可靠，故不用 pid）
  [ -f "${lock}" ] || return 0
  lt=$(read_field epoch 2>/dev/null || echo 0); [ -n "${lt}" ] || lt=0
  age=$(( $(date +%s) - lt ))
  [ "${age}" -ge "${TTL}" ]
}

write_lock() {
  mkdir -p "${lockdir}"
  {
    echo "agent=${agent}"
    echo "pid=$$"
    echo "host=$(hostname 2>/dev/null || echo unknown)"
    echo "time=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "epoch=$(date +%s)"
  } > "${lock}"
}

case "${cmd}" in
  status)
    if [ -f "${lock}" ]; then
      echo "锁: 持有中"; cat "${lock}"
      is_stale && echo "(陈旧: 可被 acquire --force 打破)"
    else
      echo "锁: 空闲 (${projroot})"
    fi
    ;;
  acquire)
    if [ -f "${lock}" ]; then
      holder=$(read_field agent 2>/dev/null || echo "?")
      if [ "${holder}" = "${agent}" ]; then
        :  # 重入：同一 agent 刷新时间戳
      elif is_stale; then
        echo "打破陈旧锁（原持有: ${holder}）" >&2
      elif [ "${FORCE}" = 1 ]; then
        echo "强制夺锁（原持有: ${holder}）" >&2
      else
        echo "锁被占用: ${holder} 持有 ${projroot} ，请等待或改为只读审核。" >&2
        exit 1
      fi
    fi
    write_lock
    echo "已取锁: ${agent} @ ${projroot}"
    ;;
  release)
    if [ -f "${lock}" ]; then
      holder=$(read_field agent 2>/dev/null || echo "?")
      if [ "${holder}" = "${agent}" ] || [ "${FORCE}" = 1 ]; then
        rm -f "${lock}"; echo "已释放: ${agent}"
      else
        echo "拒绝释放: 锁属 ${holder} ，非 ${agent}（强制用 --force）" >&2
        exit 1
      fi
    else
      echo "无锁可释放"
    fi
    ;;
esac
