# QRXfer
Transfer files from Air gapped machines using QR codes

## introduction
QRXfer is one of those "I had to give it a try" ideas. The basic idea is that it is possible to play back QR code encoded data to a receiver that may be able to reconstruct the data and reproduce the file that was originally sent.  

Think about an airgapped machine being able to generate the QR codes, you recording it with your phone, and playing it back to the receiver later.

Silly, I know.

I tested 2 main scenarios.  
The first was starting the listener on my laptop with the webcam, and the emitter on another pc (so 2 screens facing each other, not connected in *any* way). This method was the least error prone as both the sender and receiver were standing still.

The second was recording the emitter with my phone, and then placing my phone in front of the webcam with the receiver running. This was obviously much more error prone with me not being able to hold the phone still ;)

## installation
I used a [Kali Rolling](https://www.kali.org/downloads/) virtual machine with my laptops builtin Webcam added to the VMs hardware to build and test this.  
Installation on Kali is relatively simple. QRXfer uses [OpenCV](http://opencv.org/) python bindings and [Zbar](http://zbar.sourceforge.net/) python bindings for most of the magic.

  1. Install `click` with `pip install click`
  2. Install `opencv` with `apt-get install python-opencv`
  3. Install `zbar` with `apt-get install python-zbar`
  4. `git clone https://github.com/leonjza/qrxfer.git` or just grab a copy of the `qrxfer.py` script.

## usage
```
# python qrxfer.py --help
Usage: qrxfer.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  preview
  receive
  send

```

## demos
### send
The below asciicast shows how to send a file using `qrxfer.py`.  
The command used in this case was `python qrxfer.py send -s 20 -i /tmp/test_file`:

[![asciicast](https://asciinema.org/a/6arvdtdycl2mlxsp060n2u1a7.png)](https://asciinema.org/a/6arvdtdycl2mlxsp060n2u1a7)

### receive
The below asciicast shows how to receive a file using `qrxfer.py`.  
The command used in this case was `python qrxfer.py receive -d incoming`:

[![asciicast](https://asciinema.org/a/3f2vfou57yhib3l478pwow84n.png)](https://asciinema.org/a/3f2vfou57yhib3l478pwow84n)

## contact
[@leonjza](https://twitter.com/leonjza)
