"""the track: lessons, challenges, projects, what comes next - including spaced repetition."""

import os
import json
import glob

from learning import progress_tracker

from core import paths

LESSON_DIR = os.path.join(paths.resource_root(), "lessons")


def load_track(track):
    # every lesson of a track, in teaching order. broken files are skipped,
    # one bad community pack should not take the whole track down.
    lessons = []
    for path in glob.glob(os.path.join(LESSON_DIR, track, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                lesson = json.load(f)
            # a lesson is anything that yields at least one exercise (old single-quiz
            # shape or the new exercises list); challenges/projects have neither
            if lesson_exercises(lesson):
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


def lesson_by_id(track, lesson_id):
    for lesson in load_track(track):
        if lesson["id"] == lesson_id:
            return lesson
    return None


def lesson_exercises(lesson):
    # a lesson is a worked example plus a list of exercises now. old lessons had a
    # single `quiz` with lesson-level `hints`; fold that into a one-item list so
    # both shapes run through the same flow. each exercise carries its own hints.
    if lesson.get("exercises"):
        out = []
        for ex in lesson["exercises"]:
            ex = dict(ex)
            ex.setdefault("hints", [])
            out.append(ex)
        return out
    quiz = dict(lesson.get("quiz") or {})
    if not quiz:
        return []
    quiz.setdefault("hints", lesson.get("hints", []))
    return [quiz]


def review_lesson(track):
    # spaced repetition: a question missed in an earlier session, brought back
    # so the character can revisit it - "you missed this one before." returns a
    # lesson to re-ask, or None if there's nothing owed.
    for cluster, lesson_id in sorted(progress_tracker.missed_questions(track)):
        lesson = lesson_by_id(track, lesson_id)
        if lesson:
            return lesson
    return None


# -- challenges and mini projects (real code, in the user's own editor) -------

_KIND_ORDER = {"challenge": 0, "project": 1}


def load_extras(track):
    # the micro-challenges and mini projects of a track, in order: a cluster's
    # challenge before its project, clusters ascending. these are the JSON files
    # with a "function" and "cases", not a "quiz".
    items = []
    for path in glob.glob(os.path.join(LESSON_DIR, track, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                item = json.load(f)
            if "function" in item and "cases" in item:
                items.append(item)
        except (OSError, ValueError):
            continue
    items.sort(key=lambda it: (it.get("cluster", 99), _KIND_ORDER.get(it.get("kind"), 9)))
    return items


def _cluster_lessons_done(track, cluster):
    done    = progress_tracker.completed_lessons(track)
    lessons = [l for l in load_track(track) if l.get("cluster") == cluster]
    return bool(lessons) and all((str(cluster), l["id"]) in done for l in lessons)


def next_challenge(track):
    # the next thing to actually code: a cluster's challenge once its lessons are
    # done, then its project once the challenge is done. None when nothing is
    # unlocked or everything is finished.
    done_ids = progress_tracker.completed_extras(track)
    extras   = load_extras(track)
    for item in extras:
        if item["id"] in done_ids:
            continue
        if not _cluster_lessons_done(track, item["cluster"]):
            continue
        if item["kind"] == "project":
            ch = next((e for e in extras if e["cluster"] == item["cluster"]
                       and e["kind"] == "challenge"), None)
            if ch and ch["id"] not in done_ids:
                continue        # the project waits for its challenge
        return item
    return None
