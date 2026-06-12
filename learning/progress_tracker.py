"""learning_log.csv: what's done, quiz accuracy, the missed-question pool."""

import datetime

from core import datastore

LEARNING_LOG = "learning_log.csv"
FIELDS = ["date", "time", "track", "cluster", "lesson",
          "event", "correct", "hints_used", "duration_s"]

# event values: lesson_done, quiz, challenge, hint, project_done


def log_event(track, cluster, lesson, event, correct="", hints_used=0,
              duration_s=0, when=None):
    when = when or datetime.datetime.now()
    datastore.append_csv(LEARNING_LOG, FIELDS, {
        "date":       when.strftime("%Y-%m-%d"),
        "time":       when.strftime("%H:%M"),
        "track":      track,
        "cluster":    cluster,
        "lesson":     lesson,
        "event":      event,
        "correct":    correct,
        "hints_used": hints_used,
        "duration_s": int(duration_s),
    })


def read_learning_log():
    return datastore.read_csv(LEARNING_LOG)


def completed_lessons(track):
    # set of (cluster, lesson) pairs that were finished, for unlock checks
    return {(row["cluster"], row["lesson"])
            for row in read_learning_log()
            if row["track"] == track and row["event"] == "lesson_done"}


def completed_extras(track):
    # ids of the challenges and mini projects that have been passed
    return {row["lesson"] for row in read_learning_log()
            if row["track"] == track and row["event"] == "challenge_done"}


def quiz_accuracy(track, last_n=20):
    # accuracy over the recent quiz answers, None when there is nothing yet.
    # the brain reads the trend of this, not the number itself.
    answers = [row for row in read_learning_log()
               if row["track"] == track and row["event"] == "quiz"][-last_n:]
    if not answers:
        return None
    right = sum(1 for row in answers if row["correct"] == "yes")
    return right / len(answers)


def missed_questions(track):
    # what got answered wrong and never right since - the pool the character
    # pulls from when it says "you missed this one before. try it now."
    latest = {}
    for row in read_learning_log():
        if row["track"] == track and row["event"] == "quiz":
            latest[(row["cluster"], row["lesson"])] = row["correct"]
    return {key for key, correct in latest.items() if correct != "yes"}
