import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    REPO_OWNER = os.getenv('REPO_OWNER')
    REPO_NAME = os.getenv('REPO_NAME')
    TARGET_USER = os.getenv('TARGET_USER')
    
    # Polling Configuration
    POLL_INTERVAL_MINUTES = int(os.getenv('POLL_INTERVAL_MINUTES', '5'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/automator.log')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            'GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME', 'TARGET_USER'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_repo_url(cls):
        """Get repository URL"""
        return f"https://github.com/{cls.REPO_OWNER}/{cls.REPO_NAME}.git"