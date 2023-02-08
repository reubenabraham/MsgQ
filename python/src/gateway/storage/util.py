import pika, json

def upload(f, fs, channel, access):
    '''
    - uploads the file to mongodb using gridfs
    - once thats done it puts a message in rabbitmq
    '''

    try:

        fid = fs.put(f)
        # If the put is successful, it reutrns a file_id object

    except Exception as err:
        # File wasn't uploaded successfully
        return "internal server error", 500

    # Create a msg
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    # Put the msg on the queue
    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

    except Exception as err:
        print(err)
        # If the message isn't put on the queue, the mp3 that we stored in mongo will never be processed
        # Hence, delete the file in mongo- we dont want stale files in mongo.
        fs.delete(fid)
        return "internal server error", 500

