#!/usr/bin/env python
#
# Send files to zmq listener
#

import argparse
import zmq
import time
import json


def send_file(filename, host, port, timeout=600):
    """
    Send a file to the backend, encoded as json.

    Args;
        filename: name of the file to be sent
        host: Host to send the file to
        port: ZMQ port
        timeout: Timeout in s for receiving an ACK.
    """
    context = zmq.Context()
    print("Connecting to backend message server?")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://{}:{}".format(host, port))

    with open(filename, 'rb') as infile:
        fc = infile.read()
        print(" Send {} ({} bytes) ".format(filename, len(fc)))
        socket.send_string(json.dumps({"filename":filename, "payload":fc.decode() }))

    if socket.poll(timeout * 1000, zmq.POLLIN):
        print("Received reply: {}".format(socket.recv(zmq.NOBLOCK)))
        return True
    else:
        print("ERROR: TIME OUT AFTER {}s".format(timeout))

    socket.close()


def send_log_file_info(uuid, header, host, port, timeout=60):
    """
    Send info about a log file to the backend. The backend downloads the
    logfile, adds the header and starts processing. 

    Args;
        uuid: ID of the log session to download
        header: Header to be added to the log file
        host: Host to send the file to
        port: ZMQ port
        timeout: Timeout in s for receiving an ACK.
    """
    context = zmq.Context()
    print("Connecting to backend message server?")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://{}:{}".format(host, port))

    socket.send_json({"uuid": uuid, "header": header})
    #socket.send(json.dumps({"uuid": uuid, "header": header}))

    if socket.poll(timeout, zmq.POLLIN):
        print("Received reply: {}".format(socket.recv(zmq.NOBLOCK)))
        return True
    else:
        print("ERROR: TIME OUT AFTER {}s".format(timeout))

    socket.close()




if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Send content of a file via zmq")
    parser.add_argument("--host", default="10.98.64.23", help="Host to send file to.")
    parser.add_argument("--port", default=5555, help="Destination port.")
    parser.add_argument("--timeout", default=600, help="Timeout for reply.")
    parser.add_argument("file", nargs="+", help='Files to send')
    args = parser.parse_args()

    print("Sending {} files:".format(args.file))
    for i,f in enumerate(args.file):
        send_file(f, args.host, args.port, args.timeout)






