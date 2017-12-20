SCRIPT="/home/dennis/Dropbox/0cn/scripts/markdown.sh"
TARGET_DIR="/tmp/md/"

cd ../project

rm -r "$TARGET_DIR"
mkdir -p "$TARGET_DIR" && cp -ru . "$TARGET_DIR"

find . -name '*.md' |
while read filename
do
  $SCRIPT "$filename"
done

nautilus "$TARGET_DIR"
