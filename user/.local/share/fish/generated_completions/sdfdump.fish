# sdfdump
# Autogenerated from man page /usr/share/man/man1/sdfdump.1.gz
complete -c sdfdump -s h -l help -d 'Print this help message and exit'
complete -c sdfdump -s s -l summary -d 'Report a high-level summary'
complete -c sdfdump -l validate -d 'Check validity by trying to read all data values'
complete -c sdfdump -s p -l path -d 'Report only paths matching this regex'
complete -c sdfdump -s f -l field -d 'Report only fields matching this regex'
complete -c sdfdump -s t -l time -d 'Report only these times (n) or time ranges (ff. lf) for \'timeSamples\' fields'
complete -c sdfdump -l timeTolerance -d 'Report times that are close to those requested within this relative tolerance'
complete -c sdfdump -l sortBy -d 'Group output by either path or field.  Default: path'
complete -c sdfdump -l noValues -d 'Do not report field values'
complete -c sdfdump -l fullArrays -d 'Report full array contents rather than number of elements'

