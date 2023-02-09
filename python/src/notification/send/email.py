import json
import logging

log = logging.getLogger(f"{__name__}.sub")

def notification(message):
    try:
        message = json.loads(message)
        mp3_fid = message["mp3_fid"]
        log.warning(f"Your mp3 is ready for download- FID: {mp3_fid}")

    except Exception as err:
        print(err)
        return err