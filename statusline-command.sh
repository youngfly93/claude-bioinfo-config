#!/bin/bash
# Claude Code 状态栏脚本 - 显示配额使用进度条

input=$(cat)

# 获取 git 分支名（跳过可选锁，静默失败）
cwd=$(echo "$input" | jq -r '.cwd // .workspace.current_dir // empty' 2>/dev/null)
git_branch=""
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  git_branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null \
    || git -C "$cwd" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
fi

# 生成进度条函数（宽度8格）
make_bar() {
  local pct="$1"
  local filled=$(printf "%.0f" "$(echo "$pct * 8 / 100" | bc -l 2>/dev/null || echo 0)")
  [ "$filled" -gt 8 ] 2>/dev/null && filled=8
  [ "$filled" -lt 0 ] 2>/dev/null && filled=0
  local empty=$((8 - filled))
  local bar=""
  local i=0
  while [ $i -lt $filled ]; do bar="${bar}█"; i=$((i+1)); done
  while [ $i -lt 8 ]; do bar="${bar}░"; i=$((i+1)); done
  echo "$bar"
}

# 选择颜色（根据使用百分比）
pick_color() {
  local pct="$1"
  local val=$(printf "%.0f" "$pct" 2>/dev/null || echo 0)
  if [ "$val" -ge 90 ]; then
    printf '\033[31m'   # 红色
  elif [ "$val" -ge 70 ]; then
    printf '\033[33m'   # 黄色
  else
    printf '\033[32m'   # 绿色
  fi
}

RESET='\033[0m'

five_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' 2>/dev/null)
week_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' 2>/dev/null)

parts=""

# 先拼接 git 分支
if [ -n "$git_branch" ]; then
  parts="$(printf '\033[36m')${git_branch}$(printf '\033[0m')"
fi

if [ -n "$five_pct" ]; then
  bar=$(make_bar "$five_pct")
  val=$(printf "%.0f" "$five_pct")
  color=$(pick_color "$five_pct")
  [ -n "$parts" ] && parts="${parts} "
  parts="${parts}$(printf "${color}5h:[${bar}]${val}%%${RESET}")"
fi

if [ -n "$week_pct" ]; then
  bar=$(make_bar "$week_pct")
  val=$(printf "%.0f" "$week_pct")
  color=$(pick_color "$week_pct")
  [ -n "$five_pct" ] && parts="${parts} "
  parts="${parts}$(printf "${color}7d:[${bar}]${val}%%${RESET}")"
fi

if [ -n "$parts" ]; then
  printf "%b" "$parts"
fi
