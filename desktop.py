"""EchoSelf as a desktop window: the local API in a thread, a pywebview shell on top.

the window is just a frame around the same web UI that will run in a browser and on a
phone later - one face, three places. it stays offline and local: the api binds to
127.0.0.1 and nothing leaves the machine.

pywebview is an optional dependency (requirements-desktop.txt). without it we don't
fail - we tell you how to open the same thing in a browser instead. run with
`python main.py --desktop`."""

import threading

import echoself_core
from apiserver import make_server, HOST, DEFAULT_PORT


def available():
    # true only if the window toolkit is actually installed.
    try:
        import webview  # noqa: F401
        return True
    except Exception:
        return False


def launch(port=DEFAULT_PORT):
    if not available():
        print("the desktop window needs pywebview:")
        print("    pip install -r requirements-desktop.txt")
        print(f"or just run  python main.py --serve {port}  and open "
              f"http://{HOST}:{port} in any browser - it's the same companion.")
        return

    import webview

    echoself_core.prepare_environment()
    srv = make_server(port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        webview.create_window("EchoSelf", f"http://{HOST}:{port}/",
                              width=520, height=780, min_size=(380, 560))
        webview.start()
    finally:
        srv.shutdown()
