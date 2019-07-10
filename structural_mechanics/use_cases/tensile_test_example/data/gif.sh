ffmpeg -i animation.mkv -vf fps=25 frame%04d.png
gifski -o file.gif frame*.png
rm frame*.png
