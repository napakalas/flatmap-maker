#!/bin/sh

pwdCommand=$(pwd)

git clone git@github.com:napakalas/rat-flatmap.git "${pwdCommand}/alignment/flatmaps/rat-flatmap"
cd "${pwdCommand}/alignment/flatmaps/rat-flatmap" || exit
git checkout npo

cd "${pwdCommand}" || exit
git clone git@github.com:napakalas/human-flatmap.git "${pwdCommand}/alignment/flatmaps/human-flatmap"
cd "${pwdCommand}/alignment/flatmaps/human-flatmap" || exit
git checkout npo
