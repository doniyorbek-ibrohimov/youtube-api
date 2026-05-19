import logging
import sys

# Create logger
logger = logging.getLogger("youtube_clone")
logger.setLevel(logging.INFO)

# Console handler (prints to terminal)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Format: timestamp - level - message - data
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)