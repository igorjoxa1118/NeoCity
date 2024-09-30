#!/usr/bin/env bash
#atualizar(){ yad --center --entry --entry-label='Title' >> musicas.txt; }
#export -f atualizar
#tail -f musicas.txt | yad --list --column='Title' --button='Add':'bash -c atualizar'

yad --list \
  --mouse \
  --listen \
  --quoted-output \
  --regex-search \
  --grid-lines=vert \
  --grid-lines=hor \
  --selectable-labels \
  --geometry=50x50 \
  --columns 3 \
  --search-column=3 \
  --search-column=2 \
  --search-column=1 \
  --editable \
  --editable-cols=2,3 \
  --wrap-cols=3 \
  --column=Position:NUM \
  --column=Title:TEXT \
  --column=URL:TEXT \
  --tail \
  --dclick-action="mp trackgo %s" \
  --select-action="mp indice.selected %s" \
  --buttons-layout=spread \
  --button="    ":0 \
  --button="    ":10 \
  --button="    ":11 \
  --button="    ":"mp" \
  --button="    ":"@mp select.file" \
  --button="    ":"mp save" \
  --button="    ":"mp playlist.clear" \
  --button="    ":"mp prev" \
  --button=" | ":"mp pause.toggle" \
  --button="    ":"mp next"
#  ${(s:|:)"$(< /tmp/mptemp)"}
