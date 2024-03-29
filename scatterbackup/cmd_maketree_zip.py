import sys
import datetime
import zipfile

from scatterbackup.fileinfo import FileInfo
from scatterbackup.blobinfo import BlobInfo


def main() -> None:
    fileinfos = []
    with zipfile.ZipFile(sys.argv[1], 'r') as zp:
        for entry in zp.infolist():
            # print(entry, entry.filename, entry.date_time, entry.flag_bits, entry.CRC, entry.file_size)
            info = FileInfo(entry.filename)
            info.kind = 'file'
            info.size = entry.file_size
            info.blob = BlobInfo(entry.file_size, crc32=entry.CRC)
            info.mtime = int(datetime.datetime(*entry.date_time).timestamp()) * 10**9

            fileinfos.append(info)

    for info in fileinfos:
        print(info.json())


if __name__ == "__main__":
    main()


# EOF #
