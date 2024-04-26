#!/bin/bash

repo-add -n -R -q repo.db.tar.zst *.pkg.tar.zst
rm repo.db.{db,files}
cp -f repo.db.tar.zst repo.db