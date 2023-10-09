import logging

logger = logging.getLogger(__name__)
fmt = logging.Formatter('%(asctime)s - %(message)s')

logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(fmt)

logger.addHandler(console_handler)
