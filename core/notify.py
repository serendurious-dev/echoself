"""a desktop notification, the honest way: a Windows toast through PowerShell -
no dependency, nothing to install, nothing phoned out. if it can't fire (not
Windows, no PowerShell, any error), it falls back to a quiet line in the same
reminders.log the daemon already uses, so the message is never simply lost."""

import os
import datetime
import subprocess

from core import datastore

_CREATE_NO_WINDOW = 0x08000000


def _esc(s):
    # keep the text safe to drop inside a double-quoted PowerShell string
    return s.replace("`", "'").replace('"', "'").replace("\r", " ").replace("\n", " ")


def _toast_windows(title, message):
    # the built-in WinRT toast - present on Windows 10 and 11, no module needed.
    ps = (
        '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,'
        ' ContentType=WindowsRuntime] > $null;'
        '$t=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent('
        '[Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
        '$x=$t.GetElementsByTagName("text");'
        '$x.Item(0).AppendChild($t.CreateTextNode("%s")) > $null;'
        '$x.Item(1).AppendChild($t.CreateTextNode("%s")) > $null;'
        '$n=[Windows.UI.Notifications.ToastNotification]::new($t);'
        '[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('
        '"EchoSelf").Show($n);'
    ) % (_esc(title), _esc(message))
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   check=True, timeout=15,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   creationflags=_CREATE_NO_WINDOW)


def _fallback(message, when=None):
    when = when or datetime.date.today()
    os.makedirs(datastore.DATA_DIR, exist_ok=True)
    with open(os.path.join(datastore.DATA_DIR, "reminders.log"), "a", encoding="utf-8") as f:
        f.write(f"{when.isoformat()}\t{message}\n")


def notify(title, message):
    # returns True if a real toast fired, False if we fell back to the log line.
    if os.name == "nt":
        try:
            _toast_windows(title, message)
            return True
        except Exception:
            pass
    _fallback(message)
    return False
