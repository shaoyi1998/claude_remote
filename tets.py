import time
import signal
import sys
from winpty import PtyProcess
from threading import Thread, Event
import queue


class ClaudeCodeTerminal:
    def __init__(self, claude_cmd="claude"):
        """
        初始化 Claude Code 终端对话器
        claude_cmd: Claude Code 终端命令（根据实际安装情况调整）
        """
        self.claude_cmd = claude_cmd
        self.proc = None
        self.stop_event = Event()
        self.output_queue = queue.Queue()

    def start(self):
        """启动 Claude Code 进程"""
        try:
            print(f"正在启动 Claude Code ({self.claude_cmd})...")
            self.proc = PtyProcess.spawn(self.claude_cmd)

            # 等待 Claude Code 初始化完成
            time.sleep(2)

            # 读取初始欢迎信息
            initial_output = self.read_output(timeout=3)
            print("Claude Code 启动成功!")
            if initial_output:
                print("初始输出:", initial_output)
            return True
        except Exception as e:
            print(f"启动失败: {e}")
            print("请确保已安装 Claude Code 并配置到系统路径")
            print("安装命令示例: pip install claude-code-command")
            return False

    def read_output(self, timeout=1):
        """读取终端输出（非阻塞）"""
        output = ""
        try:
            # 设置非阻塞读取
            self.proc.setreadtimeout(0.1)

            while True:
                try:
                    # 尝试读取
                    chunk = self.proc.read()
                    if chunk:
                        # Claude Code 通常使用 UTF-8 编码
                        output += chunk.decode('utf-8', errors='ignore')
                except:
                    break

            return output if output else None
        except Exception as e:
            # 读取超时是正常情况
            if "timeout" not in str(e):
                print(f"读取错误: {e}")
            return output

    def send_message(self, message):
        """向 Claude Code 发送消息"""
        if not self.proc or not self.proc.isalive():
            print("进程未运行")
            return None

        # 确保消息以换行符结束
        if not message.endswith('\n'):
            message += '\n'

        # 发送消息
        self.proc.write(message.encode('utf-8'))

        # 等待 Claude 思考并响应
        time.sleep(1)  # 给 Claude 一些处理时间

        # 读取响应
        response = self.read_output(timeout=5)
        return response

    def interactive_chat(self):
        """交互式对话模式"""
        if not self.start():
            return

        print("\n" + "=" * 50)
        print("Claude Code 终端对话模式")
        print("输入 'quit' 或 'exit' 退出")
        print("=" * 50 + "\n")

        try:
            while self.proc and self.proc.isalive():
                # 获取用户输入
                user_input = input("\n你: ").strip()

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("正在退出...")
                    break

                if not user_input:
                    continue

                # 发送消息并获取响应
                print("等待 Claude 响应...")
                response = self.send_message(user_input)

                if response:
                    print("\nClaude:", response)
                else:
                    print("未收到响应")

        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"对话异常: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        if self.proc:
            try:
                # 发送退出命令
                self.proc.write(b'exit\n')
                time.sleep(0.5)

                # 终止进程
                if self.proc.isalive():
                    self.proc.terminate(force=True)
            except:
                pass

        self.stop_event.set()
        print("资源已清理")

    def run_single_query(self, query):
        """执行单次查询"""
        if not self.start():
            return None

        try:
            response = self.send_message(query)
            self.cleanup()
            return response
        except Exception as e:
            self.cleanup()
            print(f"查询错误: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    # 方法1: 交互式对话
    claude = ClaudeCodeTerminal()
    claude.interactive_chat()

    # 方法2: 单次查询（取消注释以使用）
    """
    claude = ClaudeCodeTerminal()
    query = "用Python写一个快速排序算法"
    response = claude.run_single_query(query)
    if response:
        print("Claude 的响应:")
        print(response)
    """