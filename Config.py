import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = True 
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///coinpilot.db")
    
    # Financial Configuration
    ADMIN_DEFAULT_CREDIT_BALANCE = Decimal("88988998098")
    
    # Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1")
    RATELIMIT_DEFAULT = "200 per day; 50 per hour"
    
    # EVM Settings
    DEFAULT_CONFIRMATION_BLOCKS = 2
    SUPPORTED_NETWORKS = {
        11155111: {
            "name": "Ethereum Sepolia",
            "rpc_url": os.getenv("SEPOLIA_RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com"),
            "explorer_tx_url": "https://sepolia.etherscan.io/tx/",
            "native_symbol": "ETH",
            "is_testnet": True
        },
        84532: {
            "name": "Base Sepolia",
            "rpc_url": os.getenv("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org"),
            "explorer_tx_url": "https://sepolia.basescan.org/tx/",
            "native_symbol": "ETH",
            "is_testnet": True
        }
    }

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = True
    RATELIMIT_ENABLED = Truesesesesee
