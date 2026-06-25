#start testing mediamtx
docker run --rm \
  --network surv_surv_net \
  jrottenberg/ffmpeg:4.4-alpine \
  -re \
  -f lavfi -i testsrc2=size=1280x720:rate=25 \
  -c:v libx264 \
  -preset ultrafast \
  -tune zerolatency \
  -pix_fmt yuv420p \
  -f rtsp \
  rtsp://mediamtx:8554/cam_test

  #separate tab
  curl http://localhost:9997/v3/paths/list