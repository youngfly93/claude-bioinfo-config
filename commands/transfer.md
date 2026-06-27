通过 Tailscale 将文件传输到 Windows 电脑。不要尝试 SCP/SSH/SMB，直接使用 Tailscale。

## 步骤 1：检查 Tailscale 状态

```bash
tailscale status
```

- 确认目标设备在线（状态为 `active` 或 `-`）
- 如果 tailscale 未运行，提示用户启动
- 记录目标设备名称

## 步骤 2：确认传输文件

列出要传输的文件及大小：

```bash
ls -lh <文件路径>
```

## 步骤 3：执行传输

```bash
tailscale file cp <本地文件路径> <目标设备名>:
```

- 支持多个文件：逐一传输或使用通配符
- 大文件显示传输进度

## 步骤 4：确认

传输完成后提醒用户：
- 在 Windows 端查看 Tailscale 通知
- 文件默认保存在 `Downloads` 目录

## 常见目标设备

传输时询问用户目标设备名，或从 `tailscale status` 输出中选择 Windows 设备。
