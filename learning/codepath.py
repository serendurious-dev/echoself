"""tracks and lessons: loading them, knowing which one is next.

lessons live in lessons/<track>/*.json (CC BY 4.0), one concept each, voice
neutral - the character's personality colors the delivery, not the content.
ordering comes from the cluster and lesson numbers inside the files, not
from filenames, so contributors cannot break the sequence by naming things
creatively.
"""

import os
import json
import glob

from learning import progress_tracker

LESSON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lessons")


def load_track(track):
    # every lesson of a track, in teaching order. broken files are skipped,
    # one bad community pack should not take the whole track down.
    lessons = []
    for path in glob.glob(os.path.join(LESSON_DIR, track, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                lesson = json.load(f)
            if "quiz" in lesson and "hints" in lesson:
                lessons.append(lesson)
        except (OSError, ValueError):
            continue
    lessons.sort(key=lambda l: (l.get("cluster", 99), l.get("lesson", 99)))
    return lessons


def next_lesson(track):
    # the first lesson that has not been finished yet, None when the track is
    # done. completion lives in learning_log.csv, not in the lesson files.
    done = progress_tracker.completed_lessons(track)
    for lesson in load_track(track):
        if (str(lesson.get("cluster")), lesson["id"]) not in done:
            return lesson
    return None
