import os
import zipfile
import io
import time
import datetime
from PIL import Image
import PIL


import logging

logger = logging.getLogger(__name__)

EXTS = ['JPG', 'JPEG', 'PNG']


class ProgressView:
    def __init__(self, end, message='', freq=0.01, verbose=True):
        self.name = ''
        self.end = end
        self.freq = freq
        self.verbose = verbose
        self._lastTime = 0
        self._startTime = 0

    def update(self, current):
        if not self._startTime:
            self._startTime = time.time()
        now = time.time()
        if (now - self._lastTime) > self.freq:
            if self.verbose and current > 0:
                per = (current/self.end)
                elapsedTime = now - self._startTime
                speed = current/elapsedTime if elapsedTime != 0 else 0
                predict = elapsedTime*(1-per)/per
                predict_datetime = (datetime.datetime.now() + datetime.timedelta(seconds=predict)).strftime('%Y-%m-%d %H:%M:%S')
                print('\r{} : {:>7.3f} %   {} / {}  speed:{:>.1f}/s  残り:{:>.1f}s  時刻:{}'.format(
                    self.name, per*100, current, self.end,
                    speed, predict, predict_datetime), end=' '*10)
            else:
                print('\r{} : {:>7.3f} %   {} / {}'.format(self.name, (current/self.end)*100, current, self.end), end=' '*10)
            self._lastTime = now

        if current == self.end:
            print()

def comp(base='.', imgsize=(1000, 1000), out='out.zip'):
    files = []
    arc = zipfile.ZipFile(out, 'w')

    logger.info('scan directory')
    files = getFiles(base)
    files = [i for i in files if i.split('.')[-1].upper() in EXTS]
    
    logger.info('{} files was selected'.format(len(files)))

    pv = ProgressView(len(files), 'converting')

    errCount = 0
    for i, name in enumerate(files):
        pv.update(i)

        realpath = base + os.sep + name
        res = addImage(arc, imgsize, realpath, name)
        if res != 0:
            errCount += 1
    print()

    logger.info('{} files was skipped'.format(errCount))

    arc.close()

    logger.info('complete')

    
def getFiles(path):
    files = []
    for name in os.listdir(path):
        realpath = path + os.sep + name
        if os.path.isdir(realpath):
            files.extend([name + os.sep + i2 for i2 in getFiles(realpath)])
        else:
            files.append(name)
    return files

def addImage(arc, imgsize, filepath, filename):
    logger.debug('opening file : {}'.format(filepath))
    try:
        img = Image.open(filepath)
    except Exception as e:
        logger.warning('cannot open file : {}'.format(e))
        return 1
    if img.mode != 'RGB':
        logger.debug('converting mode : {} -> {}'.format(img.mode, 'RGB'))
        img = img.convert('RGB')

    logger.debug('resizing : size {} -> {}'.format(img.size, imgsize))
    img.thumbnail(imgsize)

    logger.debug('writing to archive')
    temp = io.BytesIO()
    img.save(temp, 'jpeg')
    temp.seek(0)
    arc.writestr(filename, temp.read())
    return 0

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', '-d', default='.', type=str, help='サムネイルを作成する画像が入ったディレクトリ')
    parser.add_argument('--size', '-s', default=1000, type=int, help='リサイズするときの、縦または横の最大画像サイズ。')
    parser.add_argument('--out', '-o', default='out.zip', type=str, help='出力ファイル名')
    parser.add_argument('--log', '-l', default='info', choices=['debug', 'info'], type=str, help='表示するログレベル')
    args = parser.parse_args()

    if args.log == 'debug':
        LOGLEVEL = logging.DEBUG
    elif args.log == 'info':
        LOGLEVEL = logging.INFO
    logger = logging.getLogger(__name__)
    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(LOGLEVEL)
    streamHandler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(streamHandler)
    logger.setLevel(LOGLEVEL)


    comp(args.dir, imgsize=(args.size, args.size), out=args.out)
