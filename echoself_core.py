"""the brain without a face.

every frontend - the pygame app now, a phone or the web later - drives EchoSelf
through here and never reaches into the internals. nothing in this file renders
or assumes a screen. warm by default, private by construction: raw words are
never stored and a crisis is always handled locally.
"""


def prepare_environment(demo=False, timelapse=False):
    # demo sandbox + crash recovery, before we touch real data
    from core import datastore
    if demo:
        from core import demo_mode
        demo_mode.use_demo_dir()
        demo_mode.ensure_seeded()
        if timelapse:
            demo_mode.advance_day()
    from osutil import recovery
    recovery.audit(datastore.DATA_DIR)


def needs_onboarding():
    # no profile yet - the frontend runs its own session-zero
    from core.session_manager import load_profile
    return load_profile() is None


def today(profile=None):
    # wake the inner world, get the day's plan, fold in dark days, write a due
    # letter, measure how close you are. the answer every frontend opens to.
    from core.session_manager import load_profile
    if profile is None:
        profile = load_profile()
    from ml.behavioral_model import wake
    from ml.psychology_layer import plan_for
    from core.narrative_engine import dark_days_active
    plan = plan_for(wake())
    if dark_days_active():
        plan["expression"]  = "drift"
        plan["offer_drift"] = True
        plan["dark_days"]   = True
    from core import letters
    if letters.due():
        letters.write_monthly(profile)
    from core import echo_distance
    distance = echo_distance.compute(profile)
    return {"profile": profile, "plan": plan, "distance": distance,
            "closeness": 1.0 - sum(distance.values()) / 4.0}


def boot(demo=False, timelapse=False):
    # one-shot for a frontend with no onboarding screen of its own
    prepare_environment(demo, timelapse)
    if needs_onboarding():
        return {"needs_onboarding": True}
    return {"needs_onboarding": False, **today()}


# -- the companion, the same call from any frontend ---------------------------

def respond(text, llm=None):
    from core import companion
    return companion.respond(text, llm=llm)


def conversation(llm=None, distiller=None, now=None):
    from core import companion
    return companion.Conversation(llm=llm, distiller=distiller, now=now)


def read_emotion(text):
    from core import emotion
    return emotion.analyze(text)


def is_crisis(text):
    from core import emotion
    return emotion.is_crisis(text)


# -- where you stand ----------------------------------------------------------

def echo_distance(profile=None):
    from core import echo_distance as ed
    return ed.compute(profile)


def echo_history(days=30):
    from core import echo_distance as ed
    return ed.history(days)


# -- your data, your call -----------------------------------------------------

def export_data():
    from core import data_control
    return data_control.export()


def forget_data():
    from core import data_control
    return data_control.forget()
