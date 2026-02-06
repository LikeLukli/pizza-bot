import logging
from pathlib import Path

FORMATTER_TEMPLATE = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
        )

class BotLogger:
    """
    Simple bot logger setup.
    """
    bot_logger: logging.Logger

    def __init__(self, log_dir: str, filename: str = "bot.log", formatter=FORMATTER_TEMPLATE, logging_level=logging.DEBUG):

        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)

        # Configure ROOT logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging_level)

        # Avoid duplicate handlers if BotLogger() is constructed multiple times
        if not root_logger.handlers:
            file_handler = logging.FileHandler(
                filename=log_dir_path / filename,
                encoding="utf-8",
            )
            file_handler.setLevel(logging_level)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging_level)

            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

        # Convenience logger for bot.py (propagates to root)
        self.bot_logger = logging.getLogger("pizza_bot")
        self.bot_logger.setLevel(logging_level)
        self.bot_logger.propagate = True