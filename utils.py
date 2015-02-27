from weakref import proxy, WeakKeyDictionary
import subprocess
import sublime

busy_frames = ['.', '..', '...']
output_handle_mappings = WeakKeyDictionary()


def debug(string):
    if False:
        print(string)


def send_self(arg):
    """ A decorator which sends a generator a reference to itself via the first
    'yield' used.
    Useful for creating generators that can leverage callback-based functions
    in a linear style, by passing their 'send' or 'next' methods as callbacks.

    Note that by default, the generator reference sent is a weak reference.
    To override this behavior, pass 'False' as the first argument to the
    decorator.
    """
    use_proxy = True

    # We either directly call this, or return it, to be called by python's
    # decorator mechanism.
    def _send_self(func):
        def send_self_wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            generator.send(None)
            if use_proxy:
                generator.send(proxy(generator))
            else:
                generator.send(generator)
        return send_self_wrapper

    # If the argument is a callable, we've been used without being directly
    # passed an arguement by the user, and thus should call _send_self directly
    if callable(arg):
        # No arguments, this is the decorator
        return _send_self(arg)
    else:
        # Someone has used @send_self(True), and thus we need to return
        # _send_self to be called indirectly.
        use_proxy = arg
        return _send_self


class FlagObject(object):

    """
    Used with loop_status_msg to signal when a status message loop should end.
    """
    break_status_loop = False

    def __init__(self):
        self.break_status_loop = False


def loop_status_msg(frames, speed, flag_obj, view=None, key=''):
    """ Creates a generator which continually sets the status text to a series
    of strings.
    Useful for creating 'animations' in the status bar.

    If a view is given, sets the status for that view only (along with an
    optional key). To stop the loop, the given flag object must have it's
    'break_status_loop' attribute set to a truthy value.
    """
    @send_self
    def loop_status_generator():
        self = yield

        # Get the correct status function
        set_timeout = sublime.set_timeout
        if view is None:
            set_status = sublime.status_message
        else:
            set_status = lambda f: view.set_status(key, f)

        # Main loop
        while not flag_obj.break_status_loop:
            for frame in frames:
                set_status(frame)
                yield set_timeout(self.next, int(speed * 1000))
        if callable(flag_obj.break_status_loop):
            flag_obj.break_status_loop()
        yield

    sublime.set_timeout(loop_status_generator, 0)


def get_output_view(tag, strategy, name, fallback_window):
    """
    Retrieves an output using the given strategy, window, and views.
    """
    window_list = sublime.windows()

    # Console Strategy
    if strategy == 'console':
        return fallback_window.get_output_panel(tag)

    # Grouped strategy
    if strategy == 'grouped':
        for window in window_list:
            view_list = window.views()
            for view in view_list:
                if view.settings().get('output_tag') == tag:
                    return window, view

    if (strategy == 'separate') or (strategy == 'grouped'):
        result = fallback_window.new_file()
        result.set_name(name)
        result.set_scratch(True)
        result.settings().set('output_tag', tag)
        return fallback_window, result


def write_to_view(view, content, clear):
    """
    Writes to a view.
    """
    edit = view.begin_edit()
    if clear or view.size() == 0:
        view.erase(edit, sublime.Region(0, view.size()))
    else:
        view.insert(edit, view.size(), "\n\n")
    view.insert(edit, view.size(), content)
    view.end_edit(edit)


def show_view(window, view, is_console=False):
    """
    Shows an output view.
    """

    # Workaround for ST2 bug

    if is_console:
        tag = view.settings().get('output_tag')
        window.run_command("show_panel", {"panel": "output." + tag})
    else:
        window.focus_view(view)


def format_tag(tag, window=None, view=None):
    view_id = ''
    buffer_id = ''
    file_name = ''
    view_name = ''
    window_id = ''

    if view is not None:
        view_id = view.id()
        buffer_id = view.id()
        file_name = view.file_name()
        view_name = view.name()

    if window is not None:
        window_id = window.id()

    return tag.format(
        view_id=view_id,
        buffer_id=buffer_id,
        file_name=file_name,
        view_name=view_name,
        window_id=window_id
    )


def view_has_nim_syntax(view=None):
    """
    Tests whether the given view (or the active view) currently has 'Nim' as
    the selected syntax.
    """
    if view is None:
        view = sublime.active_window().active_view()
    return 'nim' in view.settings().get('syntax', '').lower()


def trim_region(view, region):
    """
    Trim a region of whitespace.
    """
    text = view.substr(region)
    start = region.a + ((len(text) - 1) - (len(text.strip()) - 1))
    end = region.b - ((len(text) - 1) - (len(text.rstrip()) - 1))
    return sublime.Region(start, end)


def run_process(cmd, callback=None):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        bufsize=0
    )

    output = process.communicate()[0].decode('UTF-8')
    returncode = process.returncode

    if callback is not None:
        sublime.set_timeout(lambda: callback((output, returncode)), 0)
    else:
        return output


class NimLimeMixin(object):
    def __init__(self):
        if hasattr(self, 'load_settings'):
            self.settings = sublime.load_settings('NimLime.sublime-settings')
            self.settings.add_on_change('reload', self.load_settings)
            self.load_settings()

    def is_enabled(self, *args, **kwargs):
        return True

    def description(self, *args, **kwargs):
        return self.__doc__

    def write_to_output(self, content, source_window, source_view, name):
        tag = format_tag(self.output_tag, source_window, source_view)
        output_window, output_view = get_output_view(
            tag, self.output_method, name, source_window
        )

        write_to_view(output_view, content, self.clear_output)

        if self.show_output:
            is_console = (self.output_method == 'console')
            show_view(output_window, output_view, is_console)
