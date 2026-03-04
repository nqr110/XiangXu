"""象胥 应用入口"""
import sys

from src.app import App
from src.config import logger


def main():
    if logger:
        logger.info("象胥 启动")
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
    sys.exit(0)
