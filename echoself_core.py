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
    enable_nlp()


def enable_nlp():
    # wire the local transformer for emotion only if the user turned it on AND it's
    # installed; otherwise the lexicon stays the read. deliberate, never automatic.
    from core import settings, emotion
    if settings.get("nlp_backend") != "local":
        emotion.clear_backend()
        return False
    from core import emotion_nn
    if emotion_nn.available():
        emotion.set_backend(emotion_nn.analyze)
        return True
    return False


def nlp_active():
    from core import emotion
    return emotion._BACKEND is not None


def set_nlp(on):
    # the user's switch: turn the local transformer read on or off, and apply it now
    from core import settings
    settings.set("nlp_backend", "local" if on else "off")
    return enable_nlp()


# -- the optional webcam affect-mirror (opt-in, on-device, never stores frames) --

def mirror_available():
    from vision import capture
    return capture.available()


def mirror_enabled():
    from core import settings
    return settings.get("mirror") == "on"


def set_mirror(on):
    # the user's switch. only flips on if they opted in AND the deps are installed;
    # the actual camera only opens when a frontend starts a MirrorRunner.
    from core import settings
    if on and not mirror_available():
        return False
    settings.set("mirror", "on" if on else "off")
    return mirror_enabled()


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


# -- the warm voice -----------------------------------------------------------

def llm_available():
    # is the model layer reachable (a key + the SDK)? if not, offline answers.
    from core import llm
    return llm.available()


def companion_mode():
    return "warm" if llm_available() else "offline"


def research(query):
    # look something up, grounded, never made up. raises on failure so the
    # frontend can say so plainly rather than invent an answer.
    from core import llm
    return llm.research(query)


# -- where you stand ----------------------------------------------------------

def echo_distance(profile=None):
    from core import echo_distance as ed
    return ed.compute(profile)


def echo_history(days=30):
    from core import echo_distance as ed
    return ed.history(days)


# -- learning -----------------------------------------------------------------

def mastery_report():
    from learning import mastery
    return mastery.report()


def learning_tracks():
    from learning import mastery
    return mastery.TRACKS


def set_learning_track(track):
    from core import settings
    settings.set("learning_track", track)


# -- what she remembers (the portrait) ----------------------------------------

def portrait_facts(limit=None):
    from core import portrait
    facts = portrait.facts()
    return facts[:limit] if limit else facts


def forget_fact(fact_id):
    from core import portrait
    return portrait.forget(fact_id)


# -- your data, your call -----------------------------------------------------

def export_data():
    from core import data_control
    return data_control.export()


def forget_data():
    from core import data_control
    return data_control.forget()
