#!/bin/bash

repo-add -n -R -q repo.db.tar.zst *.pkg.tar.zst
rm repo.db.{db,files}
cp -f repo.db.tar.zst ctlos_repo.db
cp -f repo.files.tar.zst ctlos_repo.files