import sys
from jupyter_client import BlockingKernelClient
import logging
logging.basicConfig()

connection_file = sys.argv[1]

client = BlockingKernelClient()
client.log.setLevel('DEBUG')
client.load_connection_file(sys.argv[1])
client.start_channels()
client.wait_for_ready(100)

client.fork()
msg = client.shell_channel.get_msg(timeout=100)
print(msg)