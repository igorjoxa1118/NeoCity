# runc-create
# Autogenerated from man page /usr/share/man/man8/runc-create.8.gz
complete -c runc-create -l bundle -s b -d 'Path to the root of the bundle directory.  Default is current directory'
complete -c runc-create -l console-socket -d 'Path to an AF_UNIX  socket which will receive a file descriptor referencing t…'
complete -c runc-create -l pid-file -d 'Specify the file to write the initial container process\' PID to'
complete -c runc-create -l no-pivot -d 'Do not use pivot root to jail process inside rootfs'
complete -c runc-create -l no-new-keyring -d 'Do not create a new session keyring for the container'
complete -c runc-create -l preserve-fds -d 'Pass N additional file descriptors to the container (stdio + $LISTEN_FDS + N …'

