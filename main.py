from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import textwrap
import psutil
import time
import os
import datetime
import random
import asyncio
import platform

@register("astrbot_plugin_Cecilia", "Teddizen", "塞西莉亚bot自写插件", "2.1.0")
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

    @filter.command("随机数")
    async def random_number(self, event: AstrMessageEvent):
        """随机数命令，格式：！随机数 1到10"""
        message_str = event.message_str.strip()
        
        # 解析命令内容（去掉"随机数 "部分）
        content = message_str[3:].strip()  # "随机数" 是3个字符

        # 如果没有指定数字范围，默认生成0到100之间的随机数
        if content == "":
            result = random.randint(0, 100)
            yield event.plain_result(f"塞西莉亚听到了…从遥远的神明那里传来的声音，那个数字是…{result}！")
            return
        
        # 查找"到"字来分隔两个数字
        elif "到" in content:
            parts = content.split("到")
            if len(parts) >= 2:
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    
                    if start <= end:
                        result = random.randint(start, end)
                        yield event.plain_result(f"塞西莉亚听到了…从遥远的神明那里传来的声音，那个数字是…{result}！")
                        return
                    else:
                        yield event.plain_result("❌ 格式错误！起始数字不能大于结束数字")
                        return
                except ValueError:
                    pass
        
        # 格式错误，提示用户正确用法
        else:
            yield event.plain_result("❌ 格式错误！请使用：!随机数 数字到数字\n例如：!随机数 1到10")

    @filter.command("选")
    async def choose(self, event: AstrMessageEvent):
        """随机选择命令，格式：!选选项一还是选项二"""
        message_str = event.message_str.strip()
        
        # 解析 "还是" 分隔的两个选项（去掉命令名"选"后）
        content = message_str[1:] if message_str.startswith("选") else message_str
        if "还是" in content:
            options = content.split("还是")
            if len(options) >= 2:
                choice1 = options[0].strip()
                choice2 = options[1].strip()
                if choice1 and choice2:
                    result = random.choice([choice1, choice2])
                    yield event.plain_result(f"塞西莉亚建议选择：{result} 哦！")
                    return
        
        # 格式错误，提示用户正确用法
        yield event.plain_result("❌ 格式错误！请使用：!选选项一还是选项二\n例如：!选苹果还是橘子")

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
            "   ✨ 塞西莉亚bot ✨",
            "   系统资源监控面板2.0",
            "-" * 25,
            "",
            "📊 【系统概览】",
            f"• 系统信息: {platform.platform()}",
            f"• 系统运行时间: {uptime_str}",
            f"• 启动时间: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "💻 【CPU 状态】",
            f"• CPU型号: {platform.processor()}",
            f"• CPU核心数: {len(cpu_percent)}核",
            f"• 当前使用率: {cpu_avg:.1f}%",
            f"• 1分钟负载: {load_avg[0]:.2f}",
            f"• 5分钟负载: {load_avg[1]:.2f}",
            f"• 15分钟负载: {load_avg[2]:.2f}",
            "",
            "💾 【内存状态】",
            f"• 物理内存: {mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB ({mem.percent:.1f}%)",
            f"• 可用内存: {mem.available/1024**3:.2f} GB",
            f"• 交换分区: {swap.used/1024**3:.1f}GB / {swap.total/1024**3:.1f}GB ({swap.percent:.1f}%)",
            "",
            "💽 【磁盘状态】",
            f"• 根分区: {disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB ({disk.percent:.1f}%)",
            "",
            "📋 【进程列表】",
            f"• 进程总数: {len(processes)} 个",
            "-" * 25,
            f" {'PID':<6} {'进程名':<15} {'用户':<8} "
            f" {'内存(MB)':>8} {'占比':>6}",
            "-" * 25,
        ]
        
        for p in top_processes:
            lines.append(
                f" {p['pid']:<6} {p['name'][:14]:<15} {p['user'][:6]:<8} "
                f" {p['memory_mb']:>8.1f} {p['memory_percent']:>5.1f}%"
            )
        
        lines.extend([
            "-" * 25,
            "📌 Made by 哲迪君",
            "🚀 Version: 2.1.0"
        ])
        
        yield event.plain_result('\n'.join(lines))
    

    @filter.command("port")
    async def port_check(self, event: AstrMessageEvent, port: str = None):
        """/port 端口号 查询占用端口的进程"""
        logger.info(f"收到端口查询指令，端口：{port}")
        if not port or not port.isdigit():
            yield event.plain_result("❌ 用法错误，请输入：/port 数字端口\n示例：/port 6185")
            return
        
        target_port = int(port)
        if target_port < 1 or target_port > 65535:
            yield event.plain_result("❌ 端口范围必须是 1~65535")
            return

        conn_list = []
        # 遍历所有网络连接
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == target_port:
                pid = conn.pid
                proc_name = "未知进程"
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        proc_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        proc_name = "进程已结束/无权限读取"
                conn_list.append({
                    "pid": pid,
                    "proc_name": proc_name,
                    "ip": conn.laddr.ip,
                    "status": conn.status
                })
        
        if not conn_list:
            msg = f"🔍 端口 {target_port} 暂无程序占用"
        else:
            lines = [
                f"🔍 端口 {target_port} 占用详情",
                "=" * 35,
                f"{'PID':<8}{'进程名':<20}{'本地IP':<15}{'状态'}"
            ]
            for item in conn_list:
                lines.append(
                    f"{str(item['pid']):<8}{item['proc_name'][:18]:<20}{item['ip']:<15}{item['status']}"
                )
            msg = "\n".join(lines)
        
        yield event.plain_result(msg)
        
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
