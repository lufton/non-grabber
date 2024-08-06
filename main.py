import asyncio
import logging

from grabbers.griddlers_net_grabber import GriddlersNetGrabber
from grabbers.webpbn_com_grabber import WebpbnComGrabber


async def main():
    logging.basicConfig(level=logging.INFO)
    griddlers_net_grabber = GriddlersNetGrabber()
    webpbn_com_grabber = WebpbnComGrabber()

    await asyncio.gather(
        griddlers_net_grabber.grab_if_enabled(),
        webpbn_com_grabber.grab_if_enabled()
    )


if __name__ == '__main__':
    asyncio.run(main())
