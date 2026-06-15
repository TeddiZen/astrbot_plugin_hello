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
        """🐳 Docker容器系统监控 - 类似Linux top命令"""
        logger.info("接收到top请求")
        
        # ========== 获取基础系统信息 ==========
        cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
        cpu_avg = sum(cpu_percent) / len(cpu_percent) if cpu_percent else 0
        disk = psutil.disk_usage('/')
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        uptime_str = str(uptime).split('.')[0]
        
        # ========== Docker真实内存信息 ==========
        mem_limit, mem_usage, mem_percent = self.get_docker_memory_info()
        
        # ========== Bot进程详情 ==========
        bot_proc = psutil.Process()
        bot_mem_rss = bot_proc.memory_info().rss  # 物理内存
        bot_mem_vms = bot_proc.memory_info().vms  # 虚拟内存
        bot_cpu = bot_proc.cpu_percent()
        bot_threads = bot_proc.num_threads()
        bot_fd = bot_proc.num_fds()  # 打开的文件描述符
        
        # ========== 格式化输出 ==========
        result = textwrap.dedent(f"""\
            🐳 **Docker容器监控 - top**
            ━━━━━━━━━━━━━━━━━━━━
            ⏱️ 运行时间: {uptime_str}
            📅 启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}

            💻 **CPU 使用情况**
              平均负载: {cpu_avg:.1f}%
              CPU核心: {len(cpu_percent)} 核
              核心占用: {' | '.join([f'{p:.1f}%' for p in cpu_percent[:4]])}

            🧠 **内存使用 (Docker限额)**
              容器限额: {mem_limit / 1024**3:.1f} GB
              已用内存: {mem_usage / 1024**3:.2f} GB
              使用率: {mem_percent:.1f}%
              剩余可用: {(mem_limit - mem_usage) / 1024**3:.2f} GB

            💾 **磁盘使用**
              总计: {disk.total / 1024**3:.1f} GB
              已用: {disk.used / 1024**3:.1f} GB ({disk.percent}%)
              空闲: {disk.free / 1024**3:.1f} GB

            🤖 **Bot 进程详情 (PID: {bot_proc.pid})**
              CPU占用: {bot_cpu:.1f}%
              物理内存: {bot_mem_rss / 1024**2:.1f} MB
              虚拟内存: {bot_mem_vms / 1024**2:.1f} MB
              内存占比: {(bot_mem_rss / mem_limit) * 100:.1f}%
              线程数量: {bot_threads}
              文件句柄: {bot_fd}

            ━━━━━━━━━━━━━━━━━━━━
            ✨ AstrBot System Monitor
            """).strip()
        
        yield event.plain_result(result)
    
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""