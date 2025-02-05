rm -rf tracks images && mkdir tracks images
cd tracks && git init && git remote add origin https://github.com/xmp3/tracks && git branch -m $1 && git pull origin $1 && cd ..
cd images && git init && git remote add origin https://github.com/xmp3/images && git branch -m $1 && git pull origin $1 && cd ..
