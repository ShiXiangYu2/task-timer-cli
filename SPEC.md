# Task Timer CLI

命令行任务计时器 - 跟踪任务执行时间，生成日报/周报。

## 功能需求

1. **开始计时**: `timer start <task-name> [--issue=<issue-id>]`
2. **暂停计时**: `timer pause`
3. **恢复计时**: `timer resume`
4. **停止计时**: `timer stop`
5. **查看状态**: `timer status`
6. **生成日报**: `timer report today`
7. **生成周报**: `timer report week`

## 技术决策

- **语言**: Python 3.11+
- **数据存储**: `~/.task-timer/records.json`
- **输出格式**: Markdown
- **无外部依赖**: 使用标准库

## 使用示例

```bash
# 开始计时
timer start "实现登录功能" --issue=123

# 暂停
timer pause

# 恢复
timer resume

# 停止
timer stop

# 查看日报
timer report today
```