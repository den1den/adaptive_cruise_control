import math
import operator
import os
import subprocess
import time
from functools import reduce
from shutil import move

import sys
from PIL import Image
from watchdog import events
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from project.requirement_checking import process_srs
from scripts.dot_template_renderer import dot_to_png


class FileExtEventHandler(FileSystemEventHandler):
    """
    Helper to check for files with a certain extension
    """

    def __init__(self, extensions=None, filename_endings=None, file_names=None, only_modify=False):
        self.filename_endings = filename_endings
        self.extensions = extensions
        self.filenames = file_names
        self.event_types = (
            events.EVENT_TYPE_MODIFIED
        ) if only_modify else (
            events.EVENT_TYPE_MODIFIED,
            events.EVENT_TYPE_MOVED,
            events.EVENT_TYPE_CREATED,
        )

    def on_any_event(self, event):
        if event.is_directory:
            return
        change_event = event.event_type in self.event_types
        path = event.dest_path if event.event_type == events.EVENT_TYPE_MOVED else event.src_path
        filename = os.path.basename(path)
        basename, extension = os.path.splitext(filename)
        if self.extensions is not None and \
                extension not in self.extensions:
            return
        if self.filenames is not None and \
                basename not in self.filenames:
            return
        if self.filename_endings is not None and \
                len([x for x in self.filename_endings if
                     basename.endswith(x)]) == 0:
            return
        if not os.path.exists(path):
            # print("%s: (non existing file) %s" % (type(self).__name__, event))
            return
        if change_event:
            # print("%s: %s" % (type(self).__name__, event))
            self.on_changed(path)

    def on_changed(self, filename):
        pass


class DotToPng(FileExtEventHandler):
    def __init__(self):
        super().__init__(extensions=('.dot',))

    def on_changed(self, filename):
        dot_to_png(
            filename,
            filename[:-4] + '.png'
        )


class SrsHandler(FileExtEventHandler):
    def __init__(self):
        super().__init__(
            extensions=('.yaml',),
            filename_endings=('requirements', 'requirement',),
            only_modify=True
        )

    def on_changed(self, filename):
        process_srs()


class Yaml2Json(FileExtEventHandler):
    """
    *.yaml
    ->
    *.json
    """

    def __init__(self):
        super().__init__(
            extensions=('.yaml',)
        )

    def on_changed(self, filename):
        out_filename = filename[:-5] + ".json"
        with open(out_filename, 'w+') as json_f:
            # sudo npm -g install yaml2json
            if subprocess.call(['yaml2json', '--pretty', filename], stdout=json_f) != 0:
                raise Exception("Could not parse %s" % filename)
        print("Json written to %s" % out_filename)


def is_image_equal(filepath1, filepath2):
    if not os.path.exists(filepath2):
        return False
    image1 = Image.open(filepath1)
    image2 = Image.open(filepath2)
    try:
        h1 = image1.histogram()
        h2 = image2.histogram()
        rms = math.sqrt(reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, h1, h2))) / len(h1))
        return rms == 0
    except OSError as e:
        print(e, file=sys.stderr)
        return False


class DownloadImageTracker(FileExtEventHandler):
    """
    Finds all .html files in /home/dennis/Dropbox/Apps/drawio
    Moves all .png and .jpg of those files to /home/dennis/Dropbox/0cn/project/diagrams
    """

    def __init__(self):
        file_names = []
        for f in os.listdir('/home/dennis/Dropbox/Apps/drawio'):
            if f.endswith('.html'):
                f = f[:-5]
                file_names += [f]
        super().__init__(
            extensions=('.png', '.jpg',),
            file_names=file_names
        )

    def on_changed(self, filename):
        name = os.path.basename(filename)
        basename, extension = os.path.splitext(name)
        destination = os.path.join(
            '/home/dennis/Dropbox/0cn/project/diagrams', name
        )
        if not is_image_equal(filename, destination):
            move(filename, destination)
            print("Moved %s" % destination)
        else:
            os.remove(filename)
            print("No change %s" % destination)


class TmpImageTracker(FileExtEventHandler):

    def __init__(self):
        super().__init__(
            extensions=('.png', '.jpg',),
            filename_endings=('.tmp', ),
        )

    def on_changed(self, filename):
        name = os.path.basename(filename)
        basename, extension = os.path.splitext(name)
        destination = os.path.join(os.path.dirname(filename),
                                   basename.replace('.tmp', '') + extension)

        if not is_image_equal(filename, destination):
            move(filename, destination)
            print("Moved %s" % destination)
        else:
            os.remove(filename)
            print("No change %s" % destination)


if __name__ == "__main__":
    observer = Observer()
    # observer.schedule(DotToPng(), 'ISO_model', recursive=True)
    observer.schedule(Yaml2Json(), 'project', recursive=True)
    observer.schedule(DownloadImageTracker(), '/home/dennis/Downloads', recursive=True)
    observer.schedule(SrsHandler(), 'project', recursive=True)
    observer.schedule(TmpImageTracker(), 'project', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
