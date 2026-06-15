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

    @filter.command("top")
    async def top(self, event: AstrMessageEvent):
        """系统资源监控 - 类似Linux top命令"""
        logger.info("接收到top请求")
        
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_avg = sum(cpu_percent) / len(cpu_percent)
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        
        # 获取进程信息（按CPU排序取前5）
        processes = []
    
        # 第一次遍历 - 预热（必须先调用一次 cpu_percent）
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc.cpu_percent()  # 第一次调用，返回值忽略
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 等待一小段时间让系统采样
        await asyncio.sleep(0.5)
        
        # 第二次遍历 - 获取真实CPU使用率
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                cpu_p = proc.cpu_percent()
                mem_p = proc.info['memory_percent']
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': cpu_p,
                    'memory_percent': mem_p
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # 按CPU使用率排序
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:5]
            
        # 格式化输出
        uptime_str = str(uptime).split('.')[0]
        
        result = textwrap.dedent(f"""\
        🔧 **系统监控 - top**
        ━━━━━━━━━━━━━━━━
        ⏱️ 运行时间: {uptime_str}
        📅 启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}

        💻 **CPU 使用情况**
          平均: {cpu_avg:.1f}%
          核心: {' | '.join([f'{p:.1f}%' for p in cpu_percent])}

        🧠 **内存使用**
          总计: {mem.total / 1024**3:.1f} GB
          已用: {mem.used / 1024**3:.1f} GB ({mem.percent}%)
          空闲: {mem.available / 1024**3:.1f} GB
          Swap: {swap.used / 1024**3:.1f} GB / {swap.total / 1024**3:.1f} GB ({swap.percent}%)

        💾 **磁盘使用 (/)**
          总计: {disk.total / 1024**3:.1f} GB
          已用: {disk.used / 1024**3:.1f} GB ({disk.percent}%)
          空闲: {disk.free / 1024**3:.1f} GB

        📊 **Top 5 进程 (按CPU)**
        """).strip()
    
        # 追加进程列表
        for i, proc in enumerate(top_processes, 1):
            result += f"\n  {i}. {proc['name']} (PID:{proc['pid']}) - CPU:{proc['cpu_percent']:.1f}% MEM:{proc['memory_percent']:.1f}%"
        result += "\n\n━━━━━━━━━━━━━━━━" 
        yield event.plain_result(result)
    
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""