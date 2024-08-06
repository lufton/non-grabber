import configparser
from pathlib import Path

CONFIG_FILE = "config.ini"


class ConfigSection:
    def __init__(self, section):
        self.section = section
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_FILE)

    def get(self, key, default=None):
        return self.config.get(self.section, key, fallback=default)

    def get_bool(self, key, default=None):
        try:
            return self.config.getboolean(self.section, key, fallback=default)
        except ValueError:
            return default

    def get_int(self, key, default=None):
        try:
            return self.config.getint(self.section, key, fallback=default)
        except ValueError:
            return default

    def get_float(self, key, default=None):
        try:
            return self.config.getfloat(self.section, key, fallback=default)
        except ValueError:
            return default


class GeneralConfig(ConfigSection):
    def __init__(self):
        super().__init__("general")

    @property
    def puzzles_path(self):
        return Path(self.get("puzzles_path", "puzzles"))

    @property
    def retries(self):
        return self.get_int("retries", 3)


class SizesConfig(ConfigSection):
    def __init__(self):
        super().__init__("sizes")

    @property
    def xxs(self):
        return self.get_int("xxs", 5 * 5) + 1

    @property
    def xs(self):
        return self.get_int("xs", 10 * 10) + 1

    @property
    def s(self):
        return self.get_int("s", 15 * 15) + 1

    @property
    def m(self):
        return self.get_int("m", 25 * 25) + 1

    @property
    def l(self):
        return self.get_int("l", 30 * 30) + 1

    @property
    def xl(self):
        return self.get_int("xl", 40 * 40) + 1

    @property
    def xxl(self):
        return self.get_int("xxl", 1000 * 1000) + 1

    @property
    def sizes(self):
        return {
            "XXS": range(0, self.xxs),
            "XS": range(self.xxs, self.xs),
            "S": range(self.xs, self.s),
            "M": range(self.s, self.m),
            "L": range(self.m, self.l),
            "XL": range(self.l, self.xl),
            "XXL": range(self.xl, self.xxl),
        }


class BaseGraggerConfig(ConfigSection):
    @property
    def is_enabled(self):
        return self.get_bool("enabled", False)

    @property
    def delay(self):
        return self.get_int("delay", 1000) / 1000.0

    @property
    def per_page(self):
        return self.get_int("per_page", 100)

    @property
    def start_page(self):
        return self.get_int("start_page", 0)

    @property
    def count(self):
        return self.get_int("count", None)

    @property
    def title(self):
        return self.get("title")

    @property
    def author(self):
        return self.get("author")

    @property
    def min_size(self):
        return self.get("min_size", 0)

    @property
    def max_size(self):
        return self.get_int("max_size", 10000)

    @property
    def min_colors(self):
        return self.get_int("min_colors", 2)

    @property
    def max_colors(self):
        return self.get_int("max_colors", 100)

    @property
    def order(self):
        return self.get("order", 0)


class GriddlersNetConfig(BaseGraggerConfig):
    def __init__(self):
        super().__init__("griddlers.net")

    @property
    def min_points(self):
        return self.get_int("min_points", 0)

    @property
    def max_points(self):
        return self.get_int("max_points")

    @property
    def order_direction(self):
        return self.get_int("order_direction", 0)


class WebpbnComConfig(BaseGraggerConfig):
    def __init__(self):
        super().__init__("webpbn.com")

    def min_id(self):
        return self.get_int("min_id")

    @property
    def max_id(self):
        return self.get_int("max_id")

    @property
    def min_quality(self):
        return int(self.get_float("min_quality", 1) * 4)

    @property
    def max_quality(self):
        return int(self.get_float("max_quality", 5) * 4)

    @property
    def without_quality(self):
        return 1 if self.get_bool("without_quality", True) else 0

    @property
    def min_difficulty(self):
        return int(self.get_float("min_difficulty", 1) * 4)

    @property
    def max_difficulty(self):
        return int(self.get_float("max_difficulty", 5) * 4)

    @property
    def without_difficulty(self):
        return 1 if self.get_bool("without_difficulty", True) else 0

    @property
    def unique_solution(self):
        return self.get_int("unique_solution", 0)

    @property
    def guess(self):
        return self.get_int("guess", 0)


config = GeneralConfig()
SIZES = SizesConfig().sizes
