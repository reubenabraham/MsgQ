import pika, json, tempfile, os
from bson.objectid import ObjectId
import moviepy.editor


def start(message, fs_videos, fs_mp3s, channel):
    # message contains the python object version of our message.
    message = json.loads(message)

    # create an empty temp file and then write the video contents into that file.
    tf = tempfile.NamedTemporaryFile()
    # get the video from gridfs and put it in the out variable.
    out = fs_videos.get(ObjectId(message["video_fid"]))
    # add video contents to empty file
    # the read method lets us read the bytes from the file.
    tf.write(out.read())
    # create audio from temp video file
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    # close tempfile- once we close the temp file, the file will automatically be deleted.
    tf.close()

    # write audio to the file
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)

    # save file to mongo
    f = open(tf_path, "rb")
    data = f.read()
    # this is an fid object- when storing it in the message, cast it to string.
    fid = fs_mp3s.put(data)
    f.close()
    os.remove(tf_path)

    message["mp3_fid"] = str(fid)

    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        # If something went wrong here, and we dont put the message on the queue, it will not be processed
        # So remove the file from mongo as well.
        fs_mp3s.delete(fid)
        return "failed to publish message"