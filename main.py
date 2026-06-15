from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import textwrap
import psutil
import time
import os
import datetime
import asyncio

@register("helloworld", "YourName", "一个简单的 Hello World 插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"HelloWorld, {user_name}, 你发的 “{message_str}” 塞西莉亚收到啦!") # 发送一条纯文本消息

    @filter.command("help")
    async def help(self, event: AstrMessageEvent):
        """这是一个 help 指令"""
        logger.info("接收到help请求")
        yield event.image_result("https://teddizen-java-tesy.oss-cn-guangzhou.aliyuncs.com/help.png")

    def _read_cgroup_file(self, path: str) -> int:
        """读取Docker cgroup文件，获取容器真实资源"""
        try:
            with open(path, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def get_docker_memory_info(self):
        """获取Docker容器真实内存信息（通过cgroup）"""
        # cgroup v1 路径
        limit = self._read_cgroup_file('/sys/fs/cgroup/memory/memory.limit_in_bytes')
        usage = self._read_cgroup_file('/sys/fs/cgroup/memory/memory.usage_in_bytes')
        
        # cgroup v2 兼容（新版Docker）
        if not limit:
            limit = self._read_cgroup_file('/sys/fs/cgroup/memory.max')
        if not usage:
            usage = self._read_cgroup_file('/sys/fs/cgroup/memory.current')
        
        #  fallback 到系统信息
        if not limit:
            mem = psutil.virtual_memory()
            return mem.total, mem.used, mem.percent
        
        percent = (usage / limit) * 100 if limit > 0 else 0
        return limit, usage, percent

    @filter.command("top")
    async def top(self, event: AstrMessageEvent):
        """🔧 系统资源监控命令"""
        logger.info("接收到top请求")
        
        # ========== 获取系统信息 ==========
        cpu_percent = psutil.cpu_percent(interval=0.3, percpu=True)
        cpu_avg = sum(cpu_percent) / len(cpu_percent)
        load_avg = psutil.getloadavg()  # 系统1/5/15分钟负载
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        uptime_str = str(uptime).split('.')[0]
        
        # ========== 获取所有进程 ==========
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'memory_info', 'cpu_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'user': proc.info['username'] or 'root',
                    'memory_mb': proc.info['memory_info'].rss / 1024**2,
                    'memory_percent': proc.info['memory_percent'],
                    'cpu_percent': proc.info['cpu_percent']
                })
            except:
                pass
        
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        top_processes = processes[:8]
        
        # ========== 专业版输出 ==========
        lines = [
            "=" * 40,
            "🔧 **AstrBot 系统资源监控面板**",
            "=" * 40,
            "",
            "📊 **【系统概览】**",
            f"  ├─ 系统运行时间: {uptime_str}",
            f"  ├─ 启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  └─ 进程总数: {len(processes)} 个",
            "",
            "💻 **【CPU 状态】**",
            f"  ├─ 当前使用率: {cpu_avg:.1f}%",
            f"  ├─ CPU核心数: {len(cpu_percent)} 核",
            f"  ├─ 1分钟负载: {load_avg[0]:.2f}",
            f"  ├─ 5分钟负载: {load_avg[1]:.2f}",
            f"  └─ 15分钟负载: {load_avg[2]:.2f}",
            "",
            "🧠 **【内存状态】**",
            f"  ├─ 物理内存: {mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB ({mem.percent:.1f}%)",
            f"  ├─ 可用内存: {mem.available/1024**3:.2f} GB",
            f"  └─ 交换分区: {swap.used/1024**3:.1f}GB / {swap.total/1024**3:.1f}GB ({swap.percent:.1f}%)",
            "",
            "💾 **【磁盘状态】**",
            f"  └─ 根分区: {disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB ({disk.percent:.1f}%)",
            "",
            "📋 **【进程排行榜】(按内存占用 Top 8)**",
            "-" * 40,
            f"  {'PID':<6} {'进程名':<15} {'用户':<8} {'内存(MB)':>8} {'占比':>6}",
            "-" * 40,
        ]
        
        for p in top_processes:
            lines.append(
                f"  {p['pid']:<6} {p['name'][:14]:<15} {p['user'][:6]:<8} "
                f"{p['memory_mb']:>8.1f} {p['memory_percent']:>5.1f}%"
            )
        
        lines.extend([
            "-" * 40,
            "",
            "💡 提示: 加 --pid=host 可查看宿主机全部进程",
        ])
        
        yield event.plain_result('\n'.join(lines))
        
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""