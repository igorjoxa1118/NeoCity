#!/bin/bash

repo-add -n -R -q custom_repo.db.tar.zst *.pkg.tar.zst
rm custom_repo.db
cp -f custom_repo.db.tar.zst custom_repo.db