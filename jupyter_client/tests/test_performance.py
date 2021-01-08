import pytest

from jupyter_client import session as ss

from .test_session import SessionTestCase

@pytest.mark.usefixtures('benchmark')
class TestPerformance(SessionTestCase):
    @pytest.fixture(autouse=True)
    def _request_benchmark(self, benchmark):
        self.benchmark = benchmark

    def test_deserialize_performance(self):
        def run(data):
            self.session.digest_history = []
            self.session.deserialize(self.session.feed_identities(data)[1])
        content = dict(t=ss.utcnow())
        metadata = dict(t=ss.utcnow())
        self.session.auth = None
        p = self.session.msg('msg')
        msg = self.session.msg('msg', content=content, metadata=metadata, parent=p['header'])
        data = self.session.serialize(msg)
        self.benchmark(run, data)
