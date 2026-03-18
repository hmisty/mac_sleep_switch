#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rumps
import subprocess
import keyring
import os
import json
import getpass

# 定义服务名称和用户名，用于钥匙串存储
KEYRING_SERVICE = f"com.blockcoach.macsleepswitch"
KEYRING_USERNAME = f"macsleepswitch_admin"

class MacSleepToggler(rumps.App):
    def __init__(self):
        # 初始化应用，设置图标和菜单
        # 使用月亮图标作为默认图标
        super(MacSleepToggler, self).__init__("🌙", title="🌙")
        
        # 创建带图标的菜单项（emoji让菜单更直观）
        self.menu = [
            "🌙 休眠模式（合盖休眠）",
            "🚫🌙 不休眠模式（合盖运行）",
            None,  # 分隔线
            "🔑 设置密码",
            "🗑️ 清除密码",
            None,
            "ℹ️ 关于"
        ]
        
        # 启动时检查密码是否已设置
        self.check_password_on_startup()
        
        # 启动时检查当前状态（可选）
        self.check_current_mode()
    
    def check_current_mode(self):
        """检查当前系统休眠模式，并更新图标"""
        try:
            result = subprocess.run(
                "pmset -g | grep SleepDisabled",
                shell=True,
                capture_output=True,
                text=True
            )
            # 如果输出中包含"1"，表示不休眠模式已开启
            if "SleepDisabled" in result.stdout and "1" in result.stdout.split()[-1]:
                self.title = "🚫🌙"
        except:
            pass  # 忽略错误，保持默认
    
    def check_password_on_startup(self):
        """启动时检查密码，如果未设置则提示"""
        password = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if not password:
            self.show_password_dialog()
    
    def show_password_dialog(self):
        """弹出带遮罩的密码输入对话框（使用AppleScript）"""
        
        # 第一次输入密码
        password = self.get_password_with_prompt("请输入你的Mac登录密码：")
        if password is None:  # 用户取消
            return False
        
        if not password:
            rumps.alert("❌ 密码不能为空", "密码不能为空，请重新输入")
            return self.show_password_dialog()
        
        # 确认密码
        confirm_password = self.get_password_with_prompt("请再次确认密码：")
        if confirm_password is None:  # 用户取消
            return False
        
        # 验证两次密码是否一致
        if password != confirm_password:
            rumps.alert("❌ 密码不匹配", "两次输入的密码不一致，请重新输入")
            return self.show_password_dialog()
        
        # 测试密码是否正确
        if self.verify_password(password):
            # 保存到钥匙串
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, password)
            rumps.notification("✅ 成功", "", "密码已保存到钥匙串")
            return True
        else:
            rumps.alert("❌ 密码验证失败", "密码错误，无法执行sudo命令")
            return self.show_password_dialog()
    
    def get_password_with_prompt(self, prompt_text):
        """
        使用AppleScript显示带遮罩的密码输入框
        返回输入的密码，如果用户取消则返回None
        """
        applescript = f'''
        display dialog "{prompt_text}" ¬
        default answer "" ¬
        with hidden answer ¬
        buttons {{"取消", "确定"}} ¬
        default button "确定"
        
        text returned of result
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # 用户点击了取消
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def verify_password(self, password):
        """验证密码是否正确"""
        try:
            # 尝试执行一个简单的sudo命令来验证密码
            test_cmd = "sudo -k -S echo '验证成功'"
            process = subprocess.run(
                test_cmd,
                shell=True,
                input=f"{password}\n",
                text=True,
                capture_output=True,
                timeout=5
            )
            return process.returncode == 0
        except Exception:
            return False
    
    def run_sudo_command(self, command):
        """执行需要sudo权限的命令"""
        password = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if not password:
            rumps.alert("❌ 密码未设置", "请先在菜单中设置密码")
            return False
        
        try:
            # 使用 -S 参数从标准输入读取密码
            full_cmd = f"echo '{password}' | sudo -S {command}"
            result = subprocess.run(
                full_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                # 如果密码错误，清除并重新提示
                error_msg = result.stderr.lower()
                if "incorrect password" in error_msg or "密码错误" in error_msg or "sorry" in error_msg:
                    keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
                    rumps.alert("❌ 密码错误", "密码已失效，请重新设置")
                    self.show_password_dialog()
                return False
            return True
        except subprocess.TimeoutExpired:
            rumps.alert("❌ 命令执行超时")
            return False
        except Exception as e:
            rumps.alert(f"❌ 执行出错: {str(e)}")
            return False
    
    def lock_screen(self):
        """锁屏"""
        lock_cmd = 'osascript -e \'tell application "System Events" to keystroke "q" using {command down, control down}\''
        subprocess.run(lock_cmd, shell=True)
    
    @rumps.clicked("🌙 休眠模式（合盖休眠）")
    def enable_sleep(self, _):
        """切换到休眠模式"""
        success = self.run_sudo_command("pmset -a disablesleep 0")
        if success:
            self.lock_screen()
            self.title = "🌙"
            rumps.notification("✅ 休眠模式", "", "已切换到：合盖休眠模式\n🌙 现在合盖会自动休眠")
    
    @rumps.clicked("🚫🌙 不休眠模式（合盖运行）")
    def enable_no_sleep(self, _):
        """切换到不休眠模式"""
        success = self.run_sudo_command("pmset -a disablesleep 1")
        if success:
            self.lock_screen()
            self.title = "🚫🌙"
            rumps.notification("✅ 不休眠模式", "", "已切换到：合盖不休眠模式\n🚫🌙 现在合盖会保持运行")
    
    @rumps.clicked("🔑 设置密码")
    def set_password(self, _):
        """手动设置/修改密码"""
        # 先询问是否要清除旧密码
        old_password = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if old_password:
            response = rumps.alert(
                title="修改密码",
                message="是否清除现有密码并重新设置？",
                ok="是",
                cancel="否"
            )
            if response:
                keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
                self.show_password_dialog()
        else:
            self.show_password_dialog()
    
    @rumps.clicked("🗑️ 清除密码")
    def clear_password(self, _):
        """清除保存的密码"""
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            rumps.notification("✅ 已清除", "", "密码已从钥匙串中移除")
        except keyring.errors.PasswordDeleteError:
            rumps.alert("❌ 没有密码", "钥匙串中未找到保存的密码")
    
    @rumps.clicked("ℹ️ 关于")
    def about(self, _):
        """关于信息"""
        rumps.alert(
            title="🌙 睡眠切换器",
            message="版本 2.1\n\n"
                   "图标含义：\n"
                   "🌙 = 休眠模式（合盖休眠）\n"
                   "🚫🌙 = 不休眠模式（合盖运行）\n\n"
                   "功能：\n"
                   "• 一键切换合盖休眠模式\n"
                   "• 密码加密存储在钥匙串\n"
                   "• 带遮罩的密码输入框\n"
                   "• 密码二次确认"
        )


if __name__ == '__main__':
    app = MacSleepToggler()
    app.run()
