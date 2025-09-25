#!/bin/sh
cd ../
mkdir output
echo "Current directory: $(pwd)"
echo -e "`ls -al`\n"
cp -R ./EVolution/* ./output
cp -R ./output ./EVolution/