markdown $1 > /tmp/$1.html
markdown-to-slides $1 -i --template assets/template_16_9.html --style assets/style.css -o /tmp/$1.s.html
cp -ruv images/ /tmp/
cp -ruv assets/ /tmp/
if [ -z "$2" ]
then
firefox /tmp/$1.s.html &
else
echo "Not showing"
fi
