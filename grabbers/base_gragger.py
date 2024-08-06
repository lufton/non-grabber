import string
from abc import abstractmethod, ABC

from config import SIZES


class BaseGrabber(ABC):
    config = None

    @abstractmethod
    async def grab(self):
        pass

    async def grab_if_enabled(self):
        if self.config.is_enabled:
            await self.grab()

    @staticmethod
    def escape_filename(name):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        name = ''.join(c for c in name if c in valid_chars)
        return name.replace(' ', '_')

    @staticmethod
    def get_size(size):
        for s, r in SIZES.items():
            if size[0] * size[1] in r:
                return s
        return f"{size[0]}x{size[1]}"
