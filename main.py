#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索互赞机器人
功能：搜索用户 + 自动点赞作品
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

import subprocess
import time
import random
import threading
from datetime import datetime

class SearchLikeBot(App):
    def __init__(self):
        super().__init__()
        self.title = "搜索互赞机器人"
        
        # 数据存储
        self.store = JsonStore('search_like_bot_config.json')
        
        # 机器人状态
        self.is_running = False
        self.current_task = "待机中"
        self.progress = 0
        self.total_users = 0
        self.completed_users = 0
        self.total_likes = 0
        self.current_cycle = 1
        self.users_since_restart = 0
        self.app_restarts = 0  # 添加APP重启计数
        
        # APP配置
        self.app_configs = {
            '抖音': {
                'package': 'com.ss.android.ugc.aweme',
                'activity': '.main.MainActivity'
            },
            '小红书': {
                'package': 'com.xingin.xhs',
                'activity': '.activity.SplashActivity'
            },
            '快手': {
                'package': 'com.smile.gifmaker',
                'activity': '.MainActivity'
            }
        }
        
        # 配置参数
        self.config = {
            'target_app': '抖音',  # 默认目标APP
            'app_package': 'com.ss.android.ugc.aweme',
            'app_activity': '.main.MainActivity',
            'user_ids': [],
            'likes_per_user': 1,  # 每个用户只点赞最新作品
            'delay_min': 2,
            'delay_max': 5,
            'app_restart_interval': 1,  # 每个用户后都重启
            'cycle_count': 1,
            'enable_app_restart': True,
            'enable_volume_key_stop': True,
            
            # 坐标配置 (基于1260x2800分辨率)
            'coordinates': {
                'search_btn': {'x': 630, 'y': 140},
                'search_input': {'x': 630, 'y': 200},
                'search_execute': {'x': 630, 'y': 280},
                'user_tab': {'x': 230, 'y': 350},
                'first_user_result': {'x': 630, 'y': 450},
                'first_work': {'x': 315, 'y': 560},
                'like_area': {'x': 630, 'y': 1400},
                'swipe_start_y': 2200,
                'swipe_end_y': 800,
                'screen_width': 1260,
                'screen_height': 2800
            }
        }
        
    def build(self):
        """构建UI界面"""
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 绑定音量键监听
        self.bind_volume_key_listener()
        
        # 标题
        title_label = Label(
            text='搜索互赞机器人 🔍💖 (音量-键停止)',
            size_hint_y=None,
            height=50,
            font_size=24
        )
        main_layout.add_widget(title_label)
        
        # 状态显示区域
        self.status_layout = self.create_status_section()
        main_layout.add_widget(self.status_layout)
        
        # 配置区域
        config_scroll = ScrollView()
        config_layout = self.create_config_section()
        config_scroll.add_widget(config_layout)
        main_layout.add_widget(config_scroll)
        
        # 控制按钮区域
        control_layout = self.create_control_section()
        main_layout.add_widget(control_layout)
        
        # 测试功能区域
        test_layout = self.create_test_section()
        main_layout.add_widget(test_layout)
        
        # 启动时加载配置
        self.load_config()
        
        return main_layout
    
    def bind_volume_key_listener(self):
        """绑定音量键监听"""
        try:
            if self.config.get('enable_volume_key_stop', True):
                threading.Thread(target=self.volume_key_listener, daemon=True).start()
                self.log_message("音量-键停止功能已启动")
        except Exception as e:
            self.log_message(f"音量键监听启动失败: {str(e)}")
    
    def volume_key_listener(self):
        """音量键监听线程"""
        try:
            possible_devices = [
                '/dev/input/event0',
                '/dev/input/event1', 
                '/dev/input/event2',
                '/dev/input/event3'
            ]
            
            device_path = None
            for device in possible_devices:
                try:
                    test_result = subprocess.run(['su', '-c', f'test -e {device}'], 
                                               capture_output=True, timeout=2)
                    if test_result.returncode == 0:
                        device_path = device
                        break
                except:
                    continue
            
            if not device_path:
                Clock.schedule_once(lambda dt: self.log_message("⚠️ 未找到可用的输入设备"))
                return
            
            Clock.schedule_once(lambda dt: self.log_message(f"🔊 音量键监听已启动"))
            
            process = subprocess.Popen(
                ['su', '-c', f'timeout 3600 getevent {device_path}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            while True:
                if not self.is_running:
                    time.sleep(1)
                    continue
                
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    line_lower = line.lower()
                    if ('key' in line_lower and 
                        ('114' in line or 'volumedown' in line_lower or 'vol_down' in line_lower) and
                        ('down' in line_lower or ' 1 ' in line)):
                        Clock.schedule_once(lambda dt: self.volume_key_stop())
                        break
                        
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.log_message(f"⚠️ 音量键检测异常: {str(e)}"))
                    break
                        
        except Exception as e:
            Clock.schedule_once(lambda dt: self.log_message(f"❌ 音量键监听启动失败: {str(e)}"))
        finally:
            try:
                if 'process' in locals():
                    process.terminate()
            except:
                pass
    
    def volume_key_stop(self):
        """音量键停止功能"""
        if self.is_running:
            self.log_message("检测到音量-键，正在停止任务...")
            self.stop_automation(None)
            self.show_popup("音量键停止", "已通过音量-键停止任务")
    
    def create_status_section(self):
        """创建状态显示区域"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=180)
        
        # 当前状态
        self.status_label = Label(
            text=f'状态: {self.current_task}',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.status_label)
        
        # 循环进度显示
        self.cycle_progress_label = Label(
            text=f'循环进度: 第{self.current_cycle}轮',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.cycle_progress_label)
        
        # 进度条
        self.progress_bar = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=20
        )
        layout.add_widget(self.progress_bar)
        
        # 用户进度文字
        self.progress_label = Label(
            text='0/0 用户',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.progress_label)
        
        # 统计信息
        self.stats_label = Label(
            text='总点赞数: 0 | 距离重启APP: 0',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.stats_label)
        
        # 日志显示
        self.log_label = Label(
            text='准备就绪，添加100个用户ID后点击开始...',
            size_hint_y=None,
            height=40,
            text_size=(None, None)
        )
        layout.add_widget(self.log_label)
        
        return layout
    
    def create_config_section(self):
        """创建配置区域"""
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # 用户ID列表配置
        users_section = BoxLayout(orientation='vertical', size_hint_y=None, height=220)
        users_section.add_widget(Label(text='100个用户ID列表 (每行一个):', size_hint_y=None, height=30))
        
        self.users_input = TextInput(
            multiline=True,
            hint_text='请输入100个用户ID，每行一个\n例如：\nuser001\nuser002\n...\nuser100',
            size_hint_y=None,
            height=170
        )
        users_section.add_widget(self.users_input)
        layout.add_widget(users_section)
        
        # APP选择设置
        app_selection_section = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        app_selection_section.add_widget(Label(text='目标APP选择:', size_hint_y=None, height=30))
        
        app_layout = GridLayout(cols=3, size_hint_y=None, height=40, spacing=5)
        
        # 抖音按钮
        self.douyin_btn = Button(
            text='抖音',
            background_color=(0.2, 0.8, 0.2, 1) if self.config['target_app'] == '抖音' else (0.5, 0.5, 0.5, 1)
        )
        self.douyin_btn.bind(on_press=lambda x: self.select_app('抖音'))
        app_layout.add_widget(self.douyin_btn)
        
        # 小红书按钮
        self.xiaohongshu_btn = Button(
            text='小红书',
            background_color=(0.8, 0.2, 0.2, 1) if self.config['target_app'] == '小红书' else (0.5, 0.5, 0.5, 1)
        )
        self.xiaohongshu_btn.bind(on_press=lambda x: self.select_app('小红书'))
        app_layout.add_widget(self.xiaohongshu_btn)
        
        # 快手按钮
        self.kuaishou_btn = Button(
            text='快手',
            background_color=(0.2, 0.2, 0.8, 1) if self.config['target_app'] == '快手' else (0.5, 0.5, 0.5, 1)
        )
        self.kuaishou_btn.bind(on_press=lambda x: self.select_app('快手'))
        app_layout.add_widget(self.kuaishou_btn)
        
        app_selection_section.add_widget(app_layout)
        layout.add_widget(app_selection_section)
        
        # 循环设置
        cycle_settings_section = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
        cycle_settings_section.add_widget(Label(text='循环设置:', size_hint_y=None, height=30))
        
        cycle_count_layout = BoxLayout(size_hint_y=None, height=40)
        cycle_count_layout.add_widget(Label(text='循环轮数:', size_hint_x=0.4))
        self.cycle_count_input = TextInput(
            text=str(self.config['cycle_count']),
            input_filter='int',
            multiline=False,
            size_hint_x=0.3
        )
        cycle_count_layout.add_widget(self.cycle_count_input)
        cycle_count_layout.add_widget(Label(text='轮', size_hint_x=0.3))
        cycle_settings_section.add_widget(cycle_count_layout)
        
        restart_interval_layout = BoxLayout(size_hint_y=None, height=40)
        restart_interval_layout.add_widget(Label(text='每处理几个用户后重启APP:', size_hint_x=0.6))
        self.restart_interval_input = TextInput(
            text=str(self.config['app_restart_interval']),
            input_filter='int',
            multiline=False,
            size_hint_x=0.4
        )
        restart_interval_layout.add_widget(self.restart_interval_input)
        cycle_settings_section.add_widget(restart_interval_layout)
        
        layout.add_widget(cycle_settings_section)
        
        # 延迟设置
        delay_section = BoxLayout(orientation='vertical', size_hint_y=None, height=120)
        delay_section.add_widget(Label(text='操作延迟设置 (秒):', size_hint_y=None, height=30))
        
        delay_min_layout = BoxLayout(size_hint_y=None, height=40)
        delay_min_layout.add_widget(Label(text='最小延迟:', size_hint_x=0.3))
        self.delay_min_input = TextInput(
            text=str(self.config['delay_min']),
            input_filter='int',
            multiline=False
        )
        delay_min_layout.add_widget(self.delay_min_input)
        delay_section.add_widget(delay_min_layout)
        
        delay_max_layout = BoxLayout(size_hint_y=None, height=40)
        delay_max_layout.add_widget(Label(text='最大延迟:', size_hint_x=0.3))
        self.delay_max_input = TextInput(
            text=str(self.config['delay_max']),
            input_filter='int',
            multiline=False
        )
        delay_max_layout.add_widget(self.delay_max_input)
        delay_section.add_widget(delay_max_layout)
        
        layout.add_widget(delay_section)
        
        return layout
    
    def create_control_section(self):
        """创建控制按钮区域"""
        layout = GridLayout(cols=2, size_hint_y=None, height=80, spacing=10)
        
        # 开始按钮
        self.start_btn = Button(
            text='开始100用户循环点赞',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.start_btn.bind(on_press=self.start_automation)
        layout.add_widget(self.start_btn)
        
        # 停止按钮
        self.stop_btn = Button(
            text='停止 (或按音量-键)',
            background_color=(0.8, 0.2, 0.2, 1),
            disabled=True
        )
        self.stop_btn.bind(on_press=self.stop_automation)
        layout.add_widget(self.stop_btn)
        
        # 保存配置按钮
        save_btn = Button(text='保存配置')
        save_btn.bind(on_press=self.save_config)
        layout.add_widget(save_btn)
        
        # 应用坐标转换按钮
        convert_btn = Button(
            text='应用目标分辨率',
            background_color=(0.2, 0.6, 0.8, 1)
        )
        convert_btn.bind(on_press=self.apply_coordinate_conversion)
        layout.add_widget(convert_btn)
        
        return layout
    
    def create_test_section(self):
        """创建测试功能区域"""
        layout = BoxLayout(orientation='vertical', size_hint_y=None, height=140, spacing=5)
        
        # 测试区域标题
        test_title = Label(
            text='🧪 测试功能区域',
            size_hint_y=None,
            height=30,
            font_size=18
        )
        layout.add_widget(test_title)
        
        # 第一行测试按钮
        test_row1 = GridLayout(cols=3, size_hint_y=None, height=50, spacing=5)
        
        # 测试搜索单个用户
        test_search_btn = Button(
            text='测试搜索第1个用户',
            background_color=(0.6, 0.4, 0.8, 1)
        )
        test_search_btn.bind(on_press=self.test_search_single_user)
        test_row1.add_widget(test_search_btn)
        
        # 测试点赞功能
        test_like_btn = Button(
            text='测试点赞最新作品',
            background_color=(0.8, 0.6, 0.4, 1)
        )
        test_like_btn.bind(on_press=self.test_like_function)
        test_row1.add_widget(test_like_btn)
        
        # 测试APP重启
        test_restart_btn = Button(
            text='测试APP重启',
            background_color=(0.8, 0.4, 0.6, 1)
        )
        test_restart_btn.bind(on_press=self.test_app_restart)
        test_row1.add_widget(test_restart_btn)
        
        layout.add_widget(test_row1)
        
        # 第二行测试按钮
        test_row2 = GridLayout(cols=3, size_hint_y=None, height=50, spacing=5)
        
        # 测试音量键
        test_volume_btn = Button(
            text='测试音量键停止',
            background_color=(0.6, 0.8, 0.4, 1)
        )
        test_volume_btn.bind(on_press=self.test_volume_key)
        test_row2.add_widget(test_volume_btn)
        
        # 测试完整流程
        test_full_btn = Button(
            text='测试完整流程',
            background_color=(0.4, 0.6, 0.8, 1)
        )
        test_full_btn.bind(on_press=self.test_full_process)
        test_row2.add_widget(test_full_btn)
        
        # 清理APP缓存
        clear_cache_btn = Button(
            text='清理APP缓存',
            background_color=(0.5, 0.5, 0.8, 1)
        )
        clear_cache_btn.bind(on_press=self.clear_app_cache)
        test_row2.add_widget(clear_cache_btn)
        
        layout.add_widget(test_row2)
        
        return layout
    
    def select_app(self, app_name):
        """选择目标APP"""
        try:
            if app_name in self.app_configs:
                self.config['target_app'] = app_name
                self.config['app_package'] = self.app_configs[app_name]['package']
                self.config['app_activity'] = self.app_configs[app_name]['activity']
                
                # 更新按钮颜色
                self.douyin_btn.background_color = (0.2, 0.8, 0.2, 1) if app_name == '抖音' else (0.5, 0.5, 0.5, 1)
                self.xiaohongshu_btn.background_color = (0.8, 0.2, 0.2, 1) if app_name == '小红书' else (0.5, 0.5, 0.5, 1)
                self.kuaishou_btn.background_color = (0.2, 0.2, 0.8, 1) if app_name == '快手' else (0.5, 0.5, 0.5, 1)
                
                self.log_message(f"📱 已选择目标APP: {app_name}")
                self.show_popup("✅ APP选择", f"已选择目标APP: {app_name}\n包名: {self.config['app_package']}")
                
        except Exception as e:
            self.log_message(f"❌ 选择APP失败: {str(e)}")
    
    def log_message(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_text = f"[{timestamp}] {message}"
        
        if hasattr(self, 'log_label') and self.log_label is not None:
            self.log_label.text = log_text
        
        print(log_text)
    
    def update_status(self, message):
        """更新状态显示"""
        self.current_task = message
        
        if hasattr(self, 'status_label') and self.status_label is not None:
            self.status_label.text = f'状态: {message}'
        
        self.log_message(message)
    
    def update_progress(self, current, total):
        """更新进度"""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress_bar.value = progress_percent
            self.progress_label.text = f'{current}/{total} 用户'
            
            self.cycle_progress_label.text = f'循环进度: 第{self.current_cycle}轮'
            
            restart_countdown = self.config['app_restart_interval'] - self.users_since_restart
            self.stats_label.text = f'总点赞数: {self.total_likes} | 距离重启APP: {restart_countdown}个用户'
    
    def save_config(self, instance):
        """保存配置"""
        try:
            self.config['user_ids'] = [
                uid.strip() for uid in self.users_input.text.split('\n') 
                if uid.strip()
            ]
            self.config['likes_per_user'] = int(self.likes_per_user_input.text or 1)
            self.config['delay_min'] = int(self.delay_min_input.text or 2)
            self.config['delay_max'] = int(self.delay_max_input.text or 5)
            self.config['cycle_count'] = int(self.cycle_count_input.text or 1)
            self.config['app_restart_interval'] = int(self.restart_interval_input.text or 1)
            
            self.store.put('config', **self.config)
            
            user_count = len(self.config['user_ids'])
            self.show_popup("成功", f"配置已保存\n用户数量: {user_count}\n循环轮数: {self.config['cycle_count']}")
            
        except Exception as e:
            self.show_popup("错误", f"保存配置失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        try:
            if self.store.exists('config'):
                saved_config = self.store.get('config')
                self.config.update(saved_config)
                
                if 'user_ids' in saved_config:
                    self.users_input.text = '\n'.join(saved_config['user_ids'])
                
                self.likes_per_user_input.text = str(self.config.get('likes_per_user', 1))
                self.delay_min_input.text = str(self.config['delay_min'])
                self.delay_max_input.text = str(self.config['delay_max'])
                self.cycle_count_input.text = str(self.config['cycle_count'])
                self.restart_interval_input.text = str(self.config.get('app_restart_interval', 1))
                
                self.log_message("配置已加载")
        except Exception as e:
            self.log_message(f"加载配置失败: {str(e)}")
    
    def show_popup(self, title, message):
        """显示弹窗"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4)
        )
        popup.open()
    
    def apply_coordinate_conversion(self, instance):
        """应用坐标转换"""
        try:
            width_scale = 2400 / 1260
            height_scale = 1080 / 2800
            
            coords = self.config['coordinates']
            for key, value in coords.items():
                if isinstance(value, dict) and 'x' in value and 'y' in value:
                    coords[key]['x'] = int(value['x'] * width_scale)
                    coords[key]['y'] = int(value['y'] * height_scale)
                elif key in ['swipe_start_y', 'swipe_end_y']:
                    coords[key] = int(value * height_scale)
            
            coords['screen_width'] = 2400
            coords['screen_height'] = 1080
            
            self.show_popup("成功", "已应用目标分辨率坐标 (2400x1080)")
            self.log_message("坐标已转换到目标分辨率")
            
        except Exception as e:
            self.show_popup("错误", f"坐标转换失败: {str(e)}")
    
    def test_search_single_user(self, instance):
        """测试搜索单个用户功能"""
        if not self.config['user_ids']:
            self.show_popup("提示", "请先添加用户ID")
            return
        
        try:
            test_user = self.config['user_ids'][0]
            self.log_message(f"🧪 测试搜索用户: {test_user}")
            threading.Thread(target=self.test_search_user_thread, args=(test_user,), daemon=True).start()
        except Exception as e:
            self.show_popup("错误", f"测试搜索失败: {str(e)}")
    
    def test_search_user_thread(self, user_id):
        """测试搜索用户线程"""
        try:
            Clock.schedule_once(lambda dt: self.update_status(f"🧪 测试搜索: {user_id}"))
            self.open_app()
            success = self.search_user(user_id)
            
            if success:
                if self.enter_user_profile():
                    Clock.schedule_once(lambda dt: self.show_popup("✅ 测试成功", f"成功搜索并进入用户主页: {user_id}"))
                else:
                    Clock.schedule_once(lambda dt: self.show_popup("⚠️ 部分成功", f"搜索成功但无法进入主页: {user_id}"))
            else:
                Clock.schedule_once(lambda dt: self.show_popup("❌ 测试失败", f"无法搜索到用户: {user_id}"))
                
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("❌ 测试错误", f"测试过程出错: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: self.update_status("测试完成，待机中"))
    
    def test_like_function(self, instance):
        """测试点赞功能"""
        try:
            self.log_message("🧪 测试点赞功能")
            threading.Thread(target=self.test_like_thread, daemon=True).start()
        except Exception as e:
            self.show_popup("错误", f"测试点赞失败: {str(e)}")
    
    def test_like_thread(self):
        """测试点赞线程"""
        try:
            Clock.schedule_once(lambda dt: self.update_status("🧪 测试双击点赞"))
            coords = self.config['coordinates']
            self.double_tap_like(coords['like_area']['x'], coords['like_area']['y'])
            Clock.schedule_once(lambda dt: self.show_popup("✅ 测试完成", "双击点赞测试完成\n请检查是否出现点赞动画"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("❌ 测试失败", f"点赞测试失败: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: self.update_status("测试完成，待机中"))
    
    def test_app_restart(self, instance):
        """测试APP重启功能"""
        try:
            self.log_message("🧪 测试APP重启")
            threading.Thread(target=self.test_restart_thread, daemon=True).start()
        except Exception as e:
            self.show_popup("错误", f"测试重启失败: {str(e)}")
    
    def test_restart_thread(self):
        """测试重启线程"""
        try:
            Clock.schedule_once(lambda dt: self.update_status("🧪 测试APP重启"))
            self.restart_app()
            Clock.schedule_once(lambda dt: self.show_popup("✅ 测试完成", "APP重启测试完成\n请检查APP是否重新启动"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("❌ 测试失败", f"重启测试失败: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: self.update_status("测试完成，待机中"))
    
    def test_volume_key(self, instance):
        """测试音量键监听功能"""
        try:
            self.log_message("🧪 测试音量键监听")
            self.is_running = True
            self.update_status("🧪 音量键测试中，请按音量-键")
            threading.Thread(target=self.volume_key_listener, daemon=True).start()
            self.show_popup("🧪 音量键测试", "测试已启动\n请按音量-键测试停止功能\n30秒后自动结束测试")
            Clock.schedule_once(self.end_volume_test, 30)
        except Exception as e:
            self.show_popup("错误", f"音量键测试失败: {str(e)}")
    
    def end_volume_test(self, dt):
        """结束音量键测试"""
        if self.is_running and self.current_task == "🧪 音量键测试中，请按音量-键":
            self.is_running = False
            self.update_status("测试超时，待机中")
            self.show_popup("⏰ 测试超时", "音量键测试已超时结束")
    
    def test_full_process(self, instance):
        """测试完整流程"""
        self.show_popup("🧪 完整流程测试", "将测试搜索用户、进入主页、点赞最新作品的完整流程")
        threading.Thread(target=self.test_full_process_thread, daemon=True).start()
    
    def test_full_process_thread(self):
        """测试完整流程线程"""
        try:
            if not self.config['user_ids']:
                Clock.schedule_once(lambda dt: self.show_popup("提示", "请先添加用户ID"))
                return
            
            test_user = self.config['user_ids'][0]
            Clock.schedule_once(lambda dt: self.update_status(f"🧪 测试完整流程: {test_user}"))
            
            self.open_app()
            time.sleep(3)
            
            if self.search_user(test_user):
                if self.enter_user_profile():
                    likes = self.like_user_works()
                    Clock.schedule_once(lambda dt: self.show_popup("✅ 测试成功", f"完整流程测试成功\n用户: {test_user}\n点赞数: {likes}"))
                else:
                    Clock.schedule_once(lambda dt: self.show_popup("⚠️ 部分成功", "搜索成功但无法进入主页"))
            else:
                Clock.schedule_once(lambda dt: self.show_popup("❌ 测试失败", "无法搜索到用户"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("❌ 测试错误", f"测试出错: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: self.update_status("测试完成，待机中"))
    
    def clear_app_cache(self, instance):
        """清理APP缓存"""
        try:
            self.log_message("🧹 清理APP缓存")
            threading.Thread(target=self.clear_cache_thread, daemon=True).start()
        except Exception as e:
            self.show_popup("错误", f"清理缓存失败: {str(e)}")
    
    def clear_cache_thread(self):
        """清理缓存线程"""
        try:
            Clock.schedule_once(lambda dt: self.update_status("🧹 正在清理APP缓存"))
            cmd = f"pm clear {self.config['app_package']}"
            subprocess.run(['su', '-c', cmd], timeout=10)
            time.sleep(2)
            Clock.schedule_once(lambda dt: self.show_popup("✅ 清理完成", "APP缓存已清理"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("❌ 清理失败", f"缓存清理失败: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: self.update_status("清理完成，待机中"))
    
    def start_automation(self, instance):
        """开始自动化"""
        if self.is_running:
            return
        
        self.save_config(None)
        
        if not self.config['user_ids']:
            self.show_popup("错误", "请先添加要点赞的用户ID列表")
            return
        
        user_count = len(self.config['user_ids'])
        if user_count == 0:
            self.show_popup("错误", "用户ID列表为空")
            return
        
        self.is_running = True
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.total_users = user_count
        self.completed_users = 0
        self.total_likes = 0
        self.current_cycle = 1
        self.users_since_restart = 0
        self.app_restarts = 0
        
        self.log_message(f"开始循环点赞任务：{user_count}个用户，{self.config['cycle_count']}轮循环")
        threading.Thread(target=self.run_automation_cycles, daemon=True).start()
    
    def stop_automation(self, instance):
        """停止自动化"""
        self.is_running = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.update_status("用户停止")
    
    def run_automation_cycles(self):
        """执行循环点赞任务"""
        try:
            user_ids = self.config['user_ids']
            cycle_count = self.config['cycle_count']
            
            Clock.schedule_once(lambda dt: self.update_status("🚀 开始用户点赞任务"))
            
            for cycle in range(1, cycle_count + 1):
                if not self.is_running:
                    break
                
                self.current_cycle = cycle
                Clock.schedule_once(lambda dt: self.log_message(f"🔄 开始第{cycle}轮循环"))
                Clock.schedule_once(lambda dt: self.update_progress(0, len(user_ids)))
                
                for i, user_id in enumerate(user_ids):
                    if not self.is_running:
                        break
                    
                    self.process_user_with_restart(user_id, i)
                    
                    if i < len(user_ids) - 1:
                        delay = random.uniform(
                            self.config['delay_min'] * 1.5,
                            self.config['delay_max'] * 2
                        )
                        time.sleep(delay)
                
                if cycle < cycle_count and self.is_running:
                    Clock.schedule_once(lambda dt: self.log_message(f"✅ 第{cycle}轮完成，休息30秒后开始下一轮"))
                    time.sleep(30)
            
            if self.is_running:
                total_expected_likes = len(user_ids) * cycle_count
                Clock.schedule_once(
                    lambda dt: self.update_status(f"🎉 所有循环完成！共{cycle_count}轮，预计点赞{total_expected_likes}次，实际点赞{self.total_likes}次")
                )
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"❌ 循环任务异常: {str(e)}"))
        finally:
            Clock.schedule_once(lambda dt: self.reset_ui_state())
    
    def process_user_with_restart(self, user_id, index):
        """处理用户并重启APP"""
        try:
            self.update_status(f"🔍 正在处理用户: {user_id}")
            
            if self.search_user(user_id):
                if self.enter_user_profile():
                    likes_count = self.like_user_works()
                    self.total_likes += likes_count
                    self.log_message(f"✅ 用户 {user_id} 点赞完成，点赞 {likes_count} 个最新作品")
                else:
                    self.log_message(f"❌ 无法进入用户 {user_id} 的主页")
            else:
                self.log_message(f"❌ 无法搜索到用户: {user_id}")
            
            if self.is_running:
                self.log_message(f"🔄 用户 {user_id} 处理完成，重启APP刷新状态")
                self.restart_app()
                self.app_restarts += 1
            
            self.completed_users += 1
            self.update_progress(self.completed_users, self.total_users)
            
        except Exception as e:
            self.log_message(f"❌ 处理用户 {user_id} 时出错: {str(e)}")
            if self.is_running:
                self.restart_app()
                self.app_restarts += 1
    
    def restart_app(self):
        """重启APP"""
        try:
            self.force_stop_app()
            time.sleep(3)
            self.open_app()
            time.sleep(5)
        except Exception as e:
            self.log_message(f"❌ 重启APP失败: {str(e)}")
    
    def force_stop_app(self):
        """强制停止APP"""
        try:
            cmd = f"am force-stop {self.config['app_package']}"
            subprocess.run(['su', '-c', cmd], timeout=10)
        except Exception as e:
            self.log_message(f"❌ 强制停止APP失败: {str(e)}")
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.is_running = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
    
    def open_app(self):
        """打开目标APP"""
        try:
            cmd = f"am start -n {self.config['app_package']}/{self.config['app_activity']}"
            subprocess.run(['su', '-c', cmd], timeout=10)
            self.human_delay(3, 5)
        except Exception as e:
            self.log_message(f"打开APP失败: {str(e)}")
    
    def search_user(self, user_id):
        """搜索用户"""
        try:
            coords = self.config['coordinates']
            
            self.log_message(f"开始搜索用户: {user_id}")
            
            self.tap_with_human_behavior(coords['search_btn']['x'], coords['search_btn']['y'])
            self.human_delay(1, 2)
            
            self.tap_with_human_behavior(coords['search_input']['x'], coords['search_input']['y'])
            self.human_delay(0.5, 1)
            
            self.clear_input()
            self.input_text(user_id)
            self.human_delay(1, 2)
            
            self.tap_with_human_behavior(coords['search_execute']['x'], coords['search_execute']['y'])
            self.human_delay(2, 4)
            
            self.tap_with_human_behavior(coords['user_tab']['x'], coords['user_tab']['y'])
            self.human_delay(1, 2)
            
            return True
            
        except Exception as e:
            self.log_message(f"搜索用户失败: {str(e)}")
            return False
    
    def enter_user_profile(self):
        """进入用户主页"""
        try:
            coords = self.config['coordinates']
            self.log_message("进入用户主页")
            self.tap_with_human_behavior(coords['first_user_result']['x'], coords['first_user_result']['y'])
            self.human_delay(3, 5)
            return True
        except Exception as e:
            self.log_message(f"进入用户主页失败: {str(e)}")
            return False
    
    def like_user_works(self):
        """点赞用户最新作品"""
        try:
            coords = self.config['coordinates']
            
            self.log_message("📱 进入作品页面，准备点赞最新作品")
            
            self.tap_with_human_behavior(coords['first_work']['x'], coords['first_work']['y'])
            self.human_delay(2, 3)
            
            self.log_message("❤️ 点赞最新作品")
            self.double_tap_like(coords['like_area']['x'], coords['like_area']['y'])
            
            self.human_delay(2, 3)
            
            self.press_back()
            self.human_delay(1, 2)
            
            return 1
            
        except Exception as e:
            self.log_message(f"❌ 点赞最新作品失败: {str(e)}")
            return 0
    
    def double_tap_like(self, x, y):
        """双击点赞"""
        try:
            self.tap_with_human_behavior(x, y)
            time.sleep(0.2)
            self.tap_with_human_behavior(x, y)
        except Exception as e:
            self.log_message(f"❌ 双击点赞失败: {str(e)}")
    
    def tap_with_human_behavior(self, x, y):
        """模拟人类点击行为"""
        try:
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            
            actual_x = max(0, x + offset_x)
            actual_y = max(0, y + offset_y)
            
            cmd = f"input tap {actual_x} {actual_y}"
            subprocess.run(['su', '-c', cmd], timeout=5)
            
            time.sleep(random.uniform(0.1, 0.3))
            
        except Exception as e:
            self.log_message(f"点击操作失败: {str(e)}")
    
    def human_swipe(self, x1, y1, x2, y2):
        """模拟人类滑动行为"""
        try:
            duration = random.randint(300, 600)
            cmd = f"input swipe {x1} {y1} {x2} {y2} {duration}"
            subprocess.run(['su', '-c', cmd], timeout=5)
        except Exception as e:
            self.log_message(f"滑动操作失败: {str(e)}")
    
    def input_text(self, text):
        """输入文字"""
        try:
            cmd = f"input text '{text}'"
            subprocess.run(['su', '-c', cmd], timeout=10)
        except Exception as e:
            self.log_message(f"输入文字失败: {str(e)}")
    
    def clear_input(self):
        """清空输入框"""
        try:
            subprocess.run(['su', '-c', 'input keyevent KEYCODE_CTRL_LEFT'], timeout=5)
            subprocess.run(['su', '-c', 'input keyevent KEYCODE_A'], timeout=5)
            subprocess.run(['su', '-c', 'input keyevent KEYCODE_DEL'], timeout=5)
        except Exception as e:
            self.log_message(f"清空输入框失败: {str(e)}")
    
    def press_back(self):
        """按返回键"""
        try:
            subprocess.run(['su', '-c', 'input keyevent KEYCODE_BACK'], timeout=5)
            self.human_delay(0.5, 1)
        except Exception as e:
            self.log_message(f"返回操作失败: {str(e)}")
    
    def human_delay(self, min_delay=None, max_delay=None):
        """人性化延迟"""
        if min_delay is None:
            min_delay = self.config['delay_min']
        if max_delay is None:
            max_delay = self.config['delay_max']
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)


# 应用入口
if __name__ == '__main__':
    SearchLikeBot().run()
