from jupyter_client.piper import EndOfOutput, PipeCapturer

ID = 'd853e19e-012f-438b-ac71-6970f49a53b7'

DATA = b"""\
foo
\0JUPYTER STREAM BEGIN d853e19e-012f-438b-ac71-6970f49a53b7
bar
baz
\0JUPYTER STREAM END d853e19e-012f-438b-ac71-6970f49a53b7
qux
"""

def test_pipe_capture_simple():
    pc = PipeCapturer('stdout')
    pc.feed(DATA)
    msgs = pc.take_queued_messages()
    for msg in msgs:
        print(msg)
    assert len(msgs) == 2
    assert msgs[0]['parent_header']['msg_id'] == ID
    assert msgs[0]['content']['name'] == 'stdout'
    assert msgs[0]['content']['text'] == 'bar\nbaz'

    assert isinstance(msgs[1], EndOfOutput)
    assert msgs[1].parent_id == ID

def test_pipe_capture_byte_by_byte():
    pc = PipeCapturer('stdout')
    for i in range(len(DATA)):
        pc.feed(DATA[i:i+1])
    msgs = pc.take_queued_messages()
    for msg in msgs:
        print(msg)
    assert len(msgs) == 2
    assert msgs[0]['parent_header']['msg_id'] == ID
    assert msgs[0]['content']['name'] == 'stdout'
    assert msgs[0]['content']['text'] == 'bar\nbaz'

    assert isinstance(msgs[-1], EndOfOutput)
    assert msgs[-1].parent_id == ID
