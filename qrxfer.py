#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2021 Konstantin Goretzki
# Copyright (c) 2016 Leon Jacobs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import base64
import hashlib
import time

import click
import cv2
import cv2.cv as cv
import numpy
import pyqrcode
import zbar

MESSAGE_BEGIN = '-----BEGIN XFER MESSAGE-----'
MESSAGE_END = '-----END XFER MESSAGE-----'
HEADER_BEGIN = '-----BEGIN XFER HEADER-----'
HEADER_END = '-----END XFER HEADER-----'


class QrSend(object):
    # The data split up into to equal sizes
    data = None

    def __init__(self, size=30, data=None):
        self.size = size
        self.data = self._chunks(data, self.size)

    def _chunks(self, l, size=None):
        n = size if size else self.size

        n = max(1, n)
        if l: return [l[i:i + n] for i in range(0, len(l), n)]

    def _headers(self):
        return [
            MESSAGE_BEGIN,
            HEADER_BEGIN,
            'LEN:{0}'.format(len(self.data)),
            'HASH:{0}'.format(hashlib.sha1(''.join(self.data)).hexdigest()),
            HEADER_END
        ]

    def _printqr(self, payload):
        data = pyqrcode.create(payload)
        print(data.terminal(quiet_zone=1))

    def send(self):

        if not self.data:
            raise Exception('No Data to Send')

        for header in self._headers():
            self._printqr(header)
            time.sleep(0.5)

        counter = 0
        for part in self.data:
            payload = '{0:010d}:{1}'.format(counter, base64.b64encode(part))
            self._printqr(payload)
            counter += 1

            print '{0}/{1}'.format(counter, len(self.data))
            time.sleep(0.2)

        self._printqr(MESSAGE_END)

    def sample_size(self, size=None):
        test_size = size if size else self.size
        data = pyqrcode.create('{0}'.format('A' * (test_size + 10)))
        print(data.terminal())


class QrReceive(object):
    window_name = 'Preview'
    data = ''
    start = False

    length = None
    hash = None
    position = 0
    received_iterations = []

    def __init__(self):
        cv.NamedWindow(self.window_name, cv.CV_WINDOW_AUTOSIZE)

        # self.capture = cv.CaptureFromCAM(camera_index) #for some reason, this doesn't work
        # self.capture = cv.CreateCameraCapture(-1)
        self.capture = cv.CaptureFromCAM(0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: Respond based on the exc_val
        self.capture = None

    def process_frames(self):

        while True:
            frame = cv.QueryFrame(self.capture)

            aframe = numpy.asarray(frame[:, :])
            g = cv.fromarray(aframe)
            g = numpy.asarray(g)

            imgray = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)

            raw = str(imgray.data)
            scanner = zbar.ImageScanner()
            scanner.parse_config('enable')

            imagezbar = zbar.Image(frame.width, frame.height, 'Y800', raw)
            scanner.scan(imagezbar)

            # Process the frames
            for symbol in imagezbar:
                if not self.process_symbol(symbol):
                    return

            # Update the preview window
            cv2.imshow(self.window_name, aframe)
            cv.WaitKey(5)

    def process_symbol(self, symbol):
        if symbol.data == MESSAGE_BEGIN:
            self.start = True
            return True

        if symbol.data == HEADER_BEGIN:
            return True

        if 'LEN' in symbol.data:
            self.length = symbol.data.split(':')[1]
            click.secho('[*] The message will come in {0} parts'.format(self.length), fg='green')
            return True

        if 'HASH' in symbol.data:
            self.hash = symbol.data.split(':')[1]
            click.secho('[*] The message has hash: {0}'.format(self.hash), fg='green')
            return True

        if symbol.data == HEADER_END:
            if not self.length or not self.hash:
                raise Exception('Header read failed. No lengh or hash data.')
            return True

        if not self.start:
            raise Exception('Received message without proper Message Start Header')

        # Cleanup On Message End
        if symbol.data == MESSAGE_END:
            # integrity check!
            final_hash = hashlib.sha1(''.join(self.data)).hexdigest()

            if final_hash != self.hash:
                click.secho('[*] Warning! Hashcheck failed!', fg='red')
                click.secho('[*] Expected: {0}, got: {1}'.format(self.hash, final_hash), fg='red', bold=True)
            else:
                click.secho('[*] Data checksum check passed.', fg='green')
            cv.DestroyWindow(self.window_name)
            return False

        iteration, data = int(symbol.data.split(':')[0]), base64.b64decode(symbol.data.split(':')[1])

        if iteration in self.received_iterations:
            return True
        else:
            self.received_iterations.append(iteration)

        if self.position != iteration:
            click.secho(
                '[*] Position lost! Transfer will fail! Expected {0} but got {1}'.format(self.position,
                                                                                         iteration), fg='red')
            self.position = iteration

        self.position += 1
        self.data = self.data + data

        click.secho('[*] {0}:{1}'.format(iteration, data), fg='green', bold=True)

        return True


@click.group()
def cli():
    pass


@cli.command()
@click.option('--size', '-s', default=30, help='Set the size to preview a QR code with.')
def preview(size):
    qr = QrSend()
    qr.sample_size(size=size)


@cli.command()
@click.option('--input', '-i', required=True, type=click.File('rb'))
@click.option('--size', '-s', default=30)
def send(input, size):
    qr = QrSend(data=input.read(), size=size)
    qr.send()


@cli.command()
@click.option('--destination', '-d', required=True, type=click.File('wb'))
def receive(destination):
    while True:

        try:
            click.secho('[*] Starting Video Capture', fg='green')

            with QrReceive() as qr:
                qr.process_frames()

            destination.write(qr.data)
            click.secho('Wrote received data to: {0}\n\n'.format(destination.name))

        except Exception as e:
            click.secho('[*] An exception occured: {0}'.format(e.message), fg='red')

        time.sleep(2)


if __name__ == '__main__':
    cli()
