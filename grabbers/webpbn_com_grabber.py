import logging
import re

import requests

from asyncio import sleep
from config import config, WebpbnComConfig
from grabbers.base_gragger import BaseGrabber
from pyquery import PyQuery as pq

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://webpbn.com"


class WebpbnComGrabber(BaseGrabber):
    def __init__(self):
        self.config = WebpbnComConfig()

    async def grab(self):
        puzzles = []
        page = self.config.start_page
        failures = 0
        while (self.config.count is None or len(puzzles) < self.config.count) and failures < config.retries:
            LOGGER.info("Delay before parsing next page")
            await sleep(self.config.delay)
            url = f"{BASE_URL}/find.cgi"
            try:
                resp = requests.post(url, {
                    "search": 1,
                    "status": 0,
                    "minid": self.config.min_id,
                    "maxid": self.config.max_id,
                    "title": self.config.title,
                    "author": self.config.author,
                    "minsize": self.config.min_size,
                    "maxsize": self.config.max_size,
                    "minqual": self.config.min_quality,
                    "maxqual": self.config.max_quality,
                    "unqual": self.config.without_quality,
                    "mindiff": self.config.min_difficulty,
                    "maxdiff": self.config.max_difficulty,
                    "undiff": self.config.without_difficulty,
                    "mincolor": self.config.min_colors,
                    "maxcolor": self.config.max_colors,
                    "uniq": self.config.unique_solution,
                    "guess": self.config.guess,
                    "blots": 2,
                    "showcreate": 1,
                    "order": self.config.order,
                    "perpage": self.config.per_page,
                    "pageno": page,
                })
                message = f"Response for page #{page} received, status code: {resp.status_code}"
                if resp.status_code == 200:
                    LOGGER.info(message)
                else:
                    raise Exception(message)
                failures = 0
                page += 1
                d = pq(resp.text)
                rows = d("form[name='search']").next_all("table").eq(0).find("tr").filter(lambda i, this: len(pq(this).find("td[colspan]")) == 0)
                if len(rows) == 0:
                    break
                for el in rows:
                    row = pq(el)
                    LOGGER.info("Delay before parsing next puzzle")
                    quality_img = row.find("td").eq(2).find("img").attr("src")
                    difficulty_img = row.find("td").eq(3).find("img").attr("src")
                    quality = int(re.match(r".*?(\d+).*", quality_img).group(1)) / 4.0
                    difficulty = int(re.match(r".*?(\d+).*", difficulty_img).group(1)) / 4.0
                    metadata = {
                        "id": row.find("td").eq(1).text().split(":")[0].replace("#", "").strip(),
                        "title": row.find("td").eq(1).text().split(":", 1)[1].strip(),
                        "author": row.find("td").eq(8).text().strip(),
                        "date": row.find("td").eq(9).text().strip().replace('\u00A0', ' '),
                        "size": list(map(int, row.find("td").eq(6).text().strip().split("x")[:2])),
                        "quality": quality,
                        "difficulty": difficulty,
                    }
                    await sleep(self.config.delay)
                    url = f"{BASE_URL}/XMLpuz.cgi"

                    while failures < config.retries:
                        try:
                            resp = requests.post(url, {
                                "id": metadata["id"]
                            })
                            message = f"Response for puzzle #{metadata["id"]} received, status code: {resp.status_code}"
                            if resp.status_code == 200:
                                LOGGER.info(message)
                            else:
                                raise Exception(message)
                            failures = 0
                            puzzleset = pq(resp.text)
                            puzzle = {
                                "metadata": metadata,
                                "data": puzzleset.find("puzzle")
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
        colors = data.find("color")
        if len(colors) == 1:
            return False
        multi_color = len(colors) > 2
        path = config.puzzles_path.joinpath("webpbn_com").joinpath(f"{len(colors)}_colors").joinpath(BaseGrabber.get_size(metadata["size"]))
        base_name = BaseGrabber.escape_filename(f"{metadata["id"]} {metadata["title"]}")
        file_path = f"{path}/{base_name}.non"
        LOGGER.info(f"Dumping puzzle #{metadata["id"]} to {file_path}")
        path.mkdir(parents=True, exist_ok=True)
        lines = [
            f"""by "{metadata["author"]}"
collection "webpbn.com"
copyright "{data.find("copyright").text()}"
date "{metadata["date"]}"
description "{data.find("description").text()}"
difficulty {metadata["difficulty"]}
height {metadata["size"][1]}
id {metadata["id"]}
link "https://webpbn.com/play.cgi?id={metadata["id"]}"
note "{data.find("note").text()}"
quality {metadata["quality"]}
title "{metadata["title"]}"
width {metadata["size"][0]}
"""]

        if multi_color:
            lines.append("\n")
            for element in colors:
                color = pq(element)
                lines.append(f"color {color.attr("name")} {color.text()} {color.attr("char")}\n")

        def dump_header():
            counts = pq(line).find("count")
            if len(counts) == 0:
                return "0\n"
            if multi_color:
                return f"{" ".join(map(lambda count: (pq(count).attr("color") or "black") + " " + pq(count).text(), counts))}\n"
            else:
                return f"{",".join(map(lambda count: pq(count).text(), counts))}\n"

        lines.append("\nrows\n")
        for line in data.find("clues[type='rows']").find("line"):
            lines.append(dump_header())

        lines.append("\ncolumns\n")
        for line in data.find("clues[type='columns']").find("line"):
            lines.append(dump_header())

        with open(file_path, "w", encoding="utf-8") as file:
            file.writelines(lines)
        return True
