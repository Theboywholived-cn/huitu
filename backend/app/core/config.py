from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database  
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Admin user
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    
    # Templates path - 使用绝对路径
    TEMPLATES_ROOT: str = r"D:\文件夹\绘图\图像代码数据汇总"
    
    # 如果TEMPLATES_ROOT以 "图像代码数据汇总" 结尾但不是完整路径，修正它
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保TEMPLATES_ROOT是绝对路径
        if self.TEMPLATES_ROOT and not (self.TEMPLATES_ROOT.startswith('/') or (len(self.TEMPLATES_ROOT) > 1 and self.TEMPLATES_ROOT[1] == ':')):
            # 相对路径，转换为绝对路径
            import os
            if 'TEMPLATES_ROOT' in os.environ:
                env_path = os.environ.get('TEMPLATES_ROOT', '')
                if env_path:
                    # 如果环境变量只包含 "图像代码数据汇总"，前缀上项目根路径
                    if env_path.endswith('图像代码数据汇总') and len(env_path) < 50:
                        self.TEMPLATES_ROOT = r"D:\文件夹\绘图\图像代码数据汇总"
    
    @property
    def TEMPLATES_PATH(self) -> str:
        return self.TEMPLATES_ROOT
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # 允许额外的字段


settings = Settings()
