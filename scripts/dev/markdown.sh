#echo "Converting $1 ($2)"
DIR=$(dirname "$1")
FILE=$(basename "$1")
TARGET_DIR="/tmp/md/"

mkdir -p "$TARGET_DIR$DIR" && cp "$1" "$TARGET_DIR$1"

# Replace empty .md links with .html links
# [A.md]() -> [A.md](A.md.html)
# Then write to tmp file and replace is successfull
sed -r -e 's/\[(.*)\.md\]\(\)/[\1.md](\1.md.html)/g' "$TARGET_DIR$1" > "$TARGET_DIR$1.tmp" && mv "$TARGET_DIR$1.tmp" "$TARGET_DIR$1"

# sudo apt-get install markdown
markdown "$TARGET_DIR$1" > "$TARGET_DIR$1.html" && echo "Output written to $TARGET_DIR$1.html"

# cp -ruv "$DIR/images/" "$TARGET_DIR$DIR"
# cp -ruv "$DIR/assets/" "$TARGET_DIR$DIR"

# if [ -z "$2" ]
# then
#   # We have an additional command, so lets show firefox
#   firefox $TARGET_DIR$1.html &
# else
#   echo "Not showing firefox"
# fi
