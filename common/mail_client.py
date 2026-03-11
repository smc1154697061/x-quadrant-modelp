import subprocess
from flask import current_app

class MailClient:
    @staticmethod
    def send_verification_code(to_email, code):
        """使用系统mail命令发送验证码"""
        subject = "验证码 - AI Chat"
        content = f"您的验证码是：{code}，有效期为5分钟。"
        
        try:
            # 使用系统mail命令发送
            cmd = f'echo "{content}" | mail -s "{subject}" {to_email}'
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception as e:
            current_app.logger.error(f"发送邮件失败: {str(e)}")
            return False
