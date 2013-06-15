import sublime

def get_window (view):
    if (view is not None):
        win = view.window();
        if win == None:
            win = sublime.active_window()
    else:
        win = sublime.active_window()
    return win


# allow windows drives
_win_start = "(?:(?:[A-Za-z][:])"
_unix_start = "(?:[/]?)" 
haxe_file_regex = "^(" + _win_start + "|" + _unix_start + ")?(?:[^:]*)):([0-9]+): (?:character(?:s?)|line(?:s?))? ([0-9]+)-?[0-9]*\s?:(.*)$"
