from codecs import getincrementaldecoder
from itertools import groupby
from operator import attrgetter

from .session import new_id, msg_header

BEGIN_LINE = b'\0JUPYTER STREAM BEGIN '
END_LINE = b'\0JUPYTER STREAM END '
BUFFER_LIMIT = 512

class EndOfOutput(object):
    """Marker for the end of output triggered by a parent message."""
    def __init__(self, parent_id):
        self.parent_id = parent_id

class Output(object):
    def __init__(self, text, parent_id):
        self.text = text
        self.parent_id = parent_id

def concat_outputs(outputs):
    for (cls, parent), group in groupby(outputs, key=lambda x: (type(x), x.parent_id)):
        if cls is Output:
            concat_text = ''.join(o.text for o in group)
            yield Output(concat_text, parent)
        else:
            # There should never be more than one consecutive end marker
            yield list(group)[0]

class PipeCapturer(object):
    """Translate output from a pipe into Jupyter stream messages."""
    def __init__(self, stream_name='stdout', username='', session_id=''):
        self.stream_name = stream_name
        self.username = username
        self.session_id = session_id
        self.buffer = b''
        self.decoder = getincrementaldecoder('utf-8')(errors='replace')
        self.current_parent_id = None
        self._queued_output = []

    def new_stream_msg(self, text, parent_id):
        msg = {}
        header = msg_header(new_id(), 'stream', self.username, self.session_id)
        parent_header = msg_header(parent_id, 'execute_request',
                                   self.username, self.session_id)
        msg['header'] = header
        msg['msg_id'] = header['msg_id']
        msg['msg_type'] = header['msg_type']
        msg['parent_header'] = parent_header
        msg['content'] = {u'name': self.stream_name, u'text': text}
        msg['metadata'] = {}
        return msg

    def _outputs_to_stream_msgs(self, outputs):
        for out in outputs:
            if isinstance(out, Output):
                yield self.new_stream_msg(out.text, out.parent_id)
            else:
                yield out

    def _queue(self, lines):
        if self.current_parent_id is None:
            return

        text = self.decoder.decode(b''.join(lines))
        if text.endswith('\n'):
            text = text[:-1]
        if not text:
            return
        self._queued_output.append(Output(text, self.current_parent_id))

    def _end_output(self, line):
        parent_id = line[len(END_LINE):].strip().decode('ascii')
        if parent_id == self.current_parent_id:
            self._queued_output.append(EndOfOutput(parent_id))
            self.current_parent_id = None

    def feed(self, data):
        """Feed data (bytes) read from the pipe from the kernel.

        After using this, call self.take_queued_messages() to get the results.
        """
        data = self.buffer + data
        self.buffer = b''
        lines = data.splitlines(keepends=True)
        if lines and not lines[-1].endswith(b'\n') and len(lines[-1]) < BUFFER_LIMIT:
            self.buffer = lines.pop()

        lines_waiting = []

        for line in lines:
            if line.startswith(BEGIN_LINE):
                self._queue(lines_waiting)
                lines_waiting = []
                self.current_parent_id = line[len(BEGIN_LINE):].strip().decode('ascii')
            elif line.startswith(END_LINE):
                self._queue(lines_waiting)
                lines_waiting = []
                self._end_output(line)
            else:
                lines_waiting.append(line)

        if lines_waiting:
            if lines_waiting[-1].endswith(b'\n'):
                self.buffer = b'\n' + self.buffer
            self._queue(lines_waiting)

    def take_queued_messages(self):
        """Get Jupyter messages from processed data"""
        outputs = concat_outputs(self._queued_output)
        messages = list(self._outputs_to_stream_msgs(outputs))
        self._queued_output = []
        return messages
