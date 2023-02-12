# MP4 → MP3 Converter

## Overview

- This project converts an uploaded video-file into a mp3 audio file.  
- This project is based on a Microservice architecture comprised of four services - `auth`,`gateway`,`converter` and `notification`.
- The API gateway and auth services are Flask servers, and the converter and notification services are RabbitMQ consumers. All services run in kubernetes pods within our local `minikube` cluster.
- The services communicate between each other with RESTful API calls.
- Before a user can use this application, they must login, and if validated, they will receive a `jwt token`- which they must supply in all subsequent API calls. The admin users are stored locally on a `mysql` database.
- The uploaded video file and the converted audio file are stored as `binary-json (bson)` objects in our local `MongoDB`.
- This project provides asynchronous inter-service communication between the `gateway` and `converter` services via a RabbitMQ message-queue. 

## Architecture and Control Flow

![Alt text](architecture.png)
![Alt text](k9s.png)

### Control Flow :

1. User hits `/login` end-point with username & password.
2. Credentials are sent to the `auth` service.
3. `auth` service validates that the credentials are legitimate.
4. `jwt` token is sent to the user.
5. User hits the `/upload` endpoint with the provided jwt as a bearer token.
6. The `gateway` service uploads the video to MongoDB.
7. Once the upload is complete, the `gateway` service puts a message (with file-id) into the video-queue.
8. The `converter` consumer pulls the message from the video queue.
9. Using the file-id, the `converter` pulls the video from MongoDB.
10. The `converter` converts the video into a MP3 and uploads it back to MongoDB.
11. The `converter` puts a message with the converted mp3 file id into the mp3 message-queue.
12. The `notification` consumer reads these messages.
13. The `notification` consumer logs the file-id so user can access it.
14. User uses the file-id and jwt to hit the `/download` end-point.
15. The `gateway` takes the file-id, and pulls the mp3 from MongoDB.
16. The mp3 is returned to the user and is downloaded locally.

## Project Dependencies
- Python 3.9+
- Docker : `brew install docker`
- Kubernetes CMD tools (kubectl) : `brew install kubectl`
- Minikube : `brew install minikube`
- Make sure the docker daemon is up, then `minikube start --driver = docker`
- K9S : `brew install k9s`
- MySQL
  - Make sure you install mysql running the same architecture of your system python, or else, some packages we use to interface with mysql will not operate correctly.
  - For instance, if you python is built for `x86` (check with `import platform`,`platform.machine()`), then first make sure your `homebrew` is `x86` homebrew and not `arm64` homebrew. 
  - `which brew` will either return `/opt/homebrew/bin/brew` (Apple Silicon/ARM64) or `/usr/local/bin/brew` (Intel x86).
  - For Arm64 Macs, you will have to specifically install x86 homebrew, add an alias in `.zshrc` as `brew86` and then `brew86 install mysql`
  - Start mysql: `brew86 services start mysql` / `brew86 services restart mysql`
  - Use the `init.sql` script to set-up mysql: `mysql -u root < init.sql`
- Create a dockerhub account, and login via CLI: `docker login -u user_name -p password docker.io`
- Make sure you have `curl` / Postman etc installed to make API calls.
- Install mongodb and `mongosh` : [Install Instructions](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/)

## Service Descriptions

### Auth Service
Checks for login credentials and returns a JWT if user is authenticated. Also helps validate whether a supplied JWT is legitimate.

### Notification Service
RabbitMQ consumer - basically reads the messages off the queue and logs the converted file-ids.

### Converter Service
RabbitMQ consumer and producer - reads messages off the video queue, picks up the file from MongoDB, converts to MP3, stores it back in MongoDB and publishes a message to the mp3 queue with the converted file-id.

### API Gateway
Services the `/login` , `/upload` and `/download` endpoints. Acts as the point of entry into the Kubernetes cluster.


## Build and Deploy a Service

- Navigate to a service directory, for example: `/python/src/auth`
- `docker build .` to build the image. Store the SHA returned at the end of the build.
- `docker tag {SHA_value} {dockerhub_username}/auth:{tag}`
- `docker push {dockerhub_username}/auth:{tag}`
- `cd` into `manifests` and `kubectl apply -f ./`
- Go into `k9s` and verify that the service is up and logs are available.
- If we want to scale-up/down replicas : `kubectl scale deployment --replicas={new_replica_number} {service_name}` 

## Running the Project
- Start-up the docker daemon.
- Ensure mysql and mongodb are up and running. Run `init.sql` as described above in the dependencies section.
- Start minikube: `minikube start`
- Add `127.0.0.1 mp3converter.com` and `127.0.0.1 rabbitmq-manager.com` in your `etc/hosts` file so that requests to those urls resolve to localhost. 
- Configure minikube to allow the ingress addon : `minikude addons enable ingress` and start a minikube tunnel: `minikube tunnel` - only with this, we can have external requests be routed to our gateway which is inside the cluster.
- Deploy the `rabbit` container.
- Go to `rabbitmq-manager.com` and create two queues: `video` and `mp3` and set them both to 'durable'.
- Deploy services in this order: `auth`, `converter`, `notification`. 
- Deploy the `gateway` service.
- Use `kubectl logs -f {service_name}` for logs to debug.
- Note- any changes to code of any service requires a image-rebuild, re-tag, push to docker repo and re-apply of kubectl. Only then will kubernetes pull the updated image while running the containers.

Now that all our services are up, lets convert a video. Download a video and put it in `python/src/converter`.

- Login : `curl -X POST http://mp3converter.com/login -u {email}:{password}` - this is the email-password combo used in `init.sql`. This returns a JWT- store it.
- Upload video : navigate to `/converter` where the video is and : `curl -X POST -F 'file=@./{video_name}.mp4' -H 'Authorization: Bearer {JWT}' http://mp3converter.com/upload`
- Go to the `notification` service logs and pick up the file-id.
- Nav to the directory where you want the mp3 and : `curl --output {require_mp3_name}.mp3 -X GET -H 'Authorization: Bearer {JWT}' "http://mp3converter.com/download?fid={file_id}"`


## Areas of Improvement

- Use an ORM like `sqlalchemy` instead of string SQL queries.
- Use github secrets to store passwords/secrets etc rather than check it in plain-text.  
- Have a smtp server mail the converted file-id to the user instead of picking it up from logs.
