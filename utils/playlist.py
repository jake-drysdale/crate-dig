# rekordbox playlist parser+writer
# m3u playlist parser+writer
# id3 tag parser+writer

import os
import mutagen
import json


def list_to_m3u(file_list, dest, pathfunc=None):
    if pathfunc is None:
        pathfunc = lambda x: x

    with open(dest, "w", encoding="utf-8") as f:
        for file in file_list:
            f.write(pathfunc(file) + "\n")


class Playlist:
    def __init__(
        self,
        mediafiles: list[str],
        savepath: str = None,
    ):
        self.mediafiles = mediafiles
        self.savepath = savepath

    def get_tags(self, mediafile: str):
        tags = {}
        audio = mutagen.File(mediafile)
        if audio is not None:
            return audio.tags.as_dict()
        return tags

    def write(self, platform="m3u", **kwargs):

        if platform == "rekordbox":
            return self.write_rekordbox(**kwargs)

        if platform == "m3u":
            return self.write_m3u(**kwargs)

        return None

    def write_rekordbox(self):
        raise NotImplementedError

    def write_m3u(self, pathfunc=None):
        print("Writing playlist")
        list_to_m3u(self.mediafiles, self.savepath, pathfunc=pathfunc)
        return self.savepath
