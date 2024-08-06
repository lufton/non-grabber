import datetime
import execjs
import logging
import requests
import urllib.parse

from asyncio import sleep
from config import config, GriddlersNetConfig
from grabbers.base_gragger import BaseGrabber
from pyquery import PyQuery as pq

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.griddlers.net/nonogram/-/g"


class GriddlersNetGrabber(BaseGrabber):
    def __init__(self):
        self.config = GriddlersNetConfig()

    async def grab(self):
        puzzles = []
        page = self.config.start_page
        failures = 0
        while (self.config.count is None or len(puzzles) < self.config.count) and failures < config.retries:
            LOGGER.info("Delay before parsing next page")
            await sleep(self.config.delay)
            url = f"{BASE_URL}/p{page}/pp{self.config.per_page}/tf/sa/va/th0/l{self.config.order}{self.config.order_direction}/s{self.config.min_size}-{self.config.max_size}/c{self.config.min_colors}-{self.config.max_colors}/p1-1/d{self.config.min_points}-{self.config.max_points or 10000000000}?_gpuzzles_WAR_puzzles_n={urllib.parse.quote(self.config.title)}&_gpuzzles_WAR_puzzles_u={urllib.parse.quote(self.config.author)}"
            try:
                resp = requests.get(url)
                message = f"Response for page #{page} received, status code: {resp.status_code}"
                if resp.status_code == 200:
                    LOGGER.info(message)
                else:
                    raise Exception(message)
                failures = 0
                page += 1
                d = pq(resp.text)
                rows = d("tr.journal-content-article")
                if len(rows) == 0:
                    break
                for el in rows:
                    row = pq(el)
                    LOGGER.info("Delay before parsing next puzzle")
                    metadata = {
                        "id": row.find("td").eq(0).text().strip(),
                        "title": row.find("td").eq(1).find("#_gpuzzles_WAR_puzzles_titleOn").text().strip(),
                        "author": row.find("td").eq(2).text().strip(),
                        "date": row.find("td").eq(3).text().strip(),
                        "size": list(map(int, row.find("td").eq(4).text().strip().split("x")[:2])),
                        "points": int(row.find("td").eq(5).text().strip().replace(",", "")),
                        "popularity": float(row.find("td").eq(6).text().strip().replace("%", "")),
                        "medium_time": row.find("td").eq(7).text().strip(),
                    }
                    await sleep(self.config.delay)
                    url = f"{BASE_URL}/?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle&_gpuzzles_WAR_puzzles_id={metadata["id"]}"

                    while failures < config.retries:
                        try:
                            resp = requests.get(url)
                            message = f"Response for puzzle #{metadata["id"]} received, status code: {resp.status_code}"
                            if resp.status_code == 200:
                                LOGGER.info(message)
                            else:
                                raise Exception(message)
                            failures = 0
                            context = execjs.compile(resp.text)
                            data = context.eval('puzzle')
                            puzzle = {
                                "metadata": metadata,
                                "data": data
                            }
                            if self.dump_puzzle(puzzle):
                                puzzles.append(puzzle)
                                LOGGER.info(f"Total {len(puzzles)} puzzles parsed")
                            else:
                                LOGGER.warning(f"Puzzle {metadata["id"]} was not parsed")
                            break
                        except Exception as er:
                            failures += 1
                            LOGGER.error(repr(er))
                    if self.config.count is not None and len(puzzles) >= self.config.count:
                        break
            except Exception as er:
                failures += 1
                LOGGER.error(repr(er))
        LOGGER.info(f"Parsing finished on page #{page - 1} with {len(puzzles)} puzzles")

    @staticmethod
    def dump_puzzle(puzzle):
        metadata = puzzle["metadata"]
        data = puzzle["data"]
        colors = data["colors"]
        used_colors = data["usedColors"]
        multi_color = len(used_colors) > 2
        path = config.puzzles_path.joinpath("griddlers_net").joinpath(f"{len(used_colors)}_colors").joinpath(BaseGrabber.get_size(metadata["size"]))
        base_name = BaseGrabber.escape_filename(f"{metadata["id"]} {metadata["title"]}")
        file_path = f"{path}/{base_name}.non"
        LOGGER.info(f"Dumping puzzle #{metadata["id"]} to {file_path}")
        path.mkdir(parents=True, exist_ok=True)
        lines = [
            f"""by "{metadata["author"]}"
collection "griddlers.net"
copyright "Copyright © 2002-{datetime.date.today().year} Griddlers.net All rights reserved."
date "{metadata["date"]}"
height {data["height"]}
id {metadata["id"]}
link "https://www.griddlers.net/nonogram/-/g/{metadata["id"]}"
medium_time "{metadata["medium_time"]}"
points {metadata["points"]}
popularity {metadata["popularity"]}
title "{metadata["title"]}"
width {data["width"]}
"""]

        if multi_color:
            lines.append("\n")
            for i, color in enumerate(colors):
                if i in used_colors:
                    lines.append(f"color {chr(i + 97)} {color.replace("#", "")}\n")

        def dump_header():
            if len(header) == 0:
                return "0\n"
            if multi_color:
                return f"{" ".join(map(lambda hint: chr(used_colors[hint[0] - 1] + 97) + " " + str(hint[1]), header))}\n"
            else:
                return f"{",".join(map(lambda hint: str(hint[1]), header))}\n"

        lines.append("\nrows\n")
        for header in data["leftHeader"]:
            lines.append(dump_header())

        lines.append("\ncolumns\n")
        for header in data["topHeader"]:
            lines.append(dump_header())

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)
        return True
