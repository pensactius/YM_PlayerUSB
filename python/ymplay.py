#!/usr/bin/env python

#
# This is a Python3 version and using pyserial library. Serial transfer
# is also decreased to 9600 bps, which is faster enough and does not
# freeze the computer.
#


import struct
import sys
import time
import serial


# Serial transmission speed. Must match bps set in Serial.begin(bps)
# at the 'ym2149_stream.ino' file.
#BAUD = 57600
BAUD = 9600


class YmReader(object):

    def __parse_extra_infos(self):
        # print(self.__fd.read(self.__header['extra_data']))
        def readcstr():
            chars = []
            while True:
                c = self.__fd.read(1)
                if c == bytes([0]):
                    return ("".join(chars))
                chars.append(c.decode())
        self.__header['song_name'] = readcstr()
        self.__header['author_name'] = readcstr()
        self.__header['song_comment'] = readcstr()

    def __parse_header(self):
        # See:
        # http://leonard.oxg.free.fr/ymformat.html
        # ftp://ftp.modland.com/pub/documents/format_documentation/Atari%20ST%20Sound%20Chip%20Emulator%20YM1-6%20(.ay,%20.ym).txt
        ym_header = '> 4s 8s I I H I H I H'
        s = self.__fd.read(struct.calcsize(ym_header))
        d = {}
        (d['id'],
         d['check_string'],
         d['nb_frames'],
         d['song_attributes'],
         d['nb_digidrums'],
         d['chip_clock'],
         d['frames_rate'],
         d['loop_frame'],
         d['extra_data'],
         ) = struct.unpack(ym_header, s)
        d['interleaved'] = d['song_attributes'] & 0x01 != 0
        self.__header = d

        # In python3 everything we read from a binary file are bytes
        # so we need to decode these to str to show them correctly.
        d['id'] = d['id'].decode()
        d['check_string'] = d['check_string'].decode()

        if self.__header['nb_digidrums'] != 0:
            raise Exception(
                'Unsupported file format: Digidrums are not supported')
        self.__parse_extra_infos()

    def __read_data_interleaved(self):
        cnt = self.__header['nb_frames']
        regs = [self.__fd.read(cnt) for i in range(16)]
        self.__data = [f for f in zip(*regs)]
    
    def __read_data_non_interleaved(self):
        cnt = self.__header['nb_frames']
        self.__data = [self.__fd.read(16) for i in range(cnt)]              

    def __read_data(self):
        if not self.__header['interleaved']:
            #raise Exception(
            #    'Unsupported file format: Only interleaved data are supported')
            self.__read_data_non_interleaved()
        else:
          self.__read_data_interleaved()

    def __check_eof(self):
        if self.__fd.read(4).decode() != 'End!':
            print('*Warning* End! marker not found after frames')

    def __init__(self, fd):
        self.__fd = fd
        self.__parse_header()
        self.__data = []

    def dump_header(self):
        for k in ('id', 'check_string', 'nb_frames', 'song_attributes',
                  'nb_digidrums', 'chip_clock', 'frames_rate', 'loop_frame',
                  'extra_data', 'song_name', 'author_name', 'song_comment'):
            print("{}: {}".format(k, self.__header[k]))

    def get_header(self):
        return self.__header

    def get_data(self):
        if not self.__data:
            self.__read_data()
            self.__check_eof()
        return self.__data


def to_minsec(frames, frames_rate):
    secs = frames // frames_rate
    mins = secs // 60
    secs = secs % 60
    return (mins, secs)


def main():
    header = None
    data = None

    if len(sys.argv) != 3:
        print("Syntax is: {} <output_device> <ym_filepath>".format(
            sys.argv[0]))
        exit(0)

    with open(sys.argv[2], 'rb') as fd:
        ym = YmReader(fd)
        ym.dump_header()
        header = ym.get_header()
        data = ym.get_data()
        #print(data[-1])

    song_min, song_sec = to_minsec(header['nb_frames'], header['frames_rate'])
    print("")

    with serial.Serial(sys.argv[1], BAUD) as ser:
        time.sleep(2)  # Wait for Arduino reset
        #frame_t = time.time()
        frame_t = time.perf_counter()

        # Send byte to set correct clock speed
        # 2 Mhz -> 3
        # 1 Mhz -> 7
        if header['chip_clock'] == 2000000:
          clk_div = 3
        elif header['chip_clock'] == 1000000:
          clk_div = 7
        else:
          raise Exception(
                'Unsupported clock speed: 1 Mhz or 2 Mhz only')
        clk_div = bytes([clk_div])
        print ("Clock divider", clk_div)
        ser.write (clk_div)        
        time.sleep(1)

        try:
            for i in range(header['nb_frames']):
                # Substract time spent in code
                #time.sleep(1. / header['frames_rate'] -
                #           (time.time() - frame_t))
                #frame_t = time.time()
                target_time = 1./ header['frames_rate']
                while (time.perf_counter() -frame_t)< target_time:
                  pass
                frame_t = time.perf_counter()
                ser.write(data[i])
                i += 1

                # Additionnal processing
                cur_min, cur_sec = to_minsec(i, header['frames_rate'])
                sys.stdout.write(
                    "\x1b[2K\rPlaying {0:02}:{1:02} / {2:02}:{3:02}".format(
                        cur_min, cur_sec, song_min, song_sec))
                sys.stdout.flush()

            # Clear YM2149 registers
            for i in range(16):
              ser.write(bytes(b'\x00'))
        except KeyboardInterrupt:
            # Clear YM2149 registers
            for i in range(16):
              ser.write(bytes(b'\x00'))
            print("\nYM2149 Registers cleared")


if __name__ == '__main__':
    main()
