# ffmpeg -r 60 -f image2 -s 1920x1080 -i anim.%04d.png -vcodec libx264 -crf 0 -pix_fmt yuv420p animation.mp4
ffmpeg -r 60 -i anim.%04d.png -c:v copy animation.mkv
