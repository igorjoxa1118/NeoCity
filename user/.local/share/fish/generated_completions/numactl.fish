# numactl
# Autogenerated from man page /usr/share/man/man8/numactl.8.gz
complete -c numactl -l all -s a -d 'Unset default cpuset awareness, so user can use all possible CPUs/nodes for f…'
complete -c numactl -l interleave -s i -d 'Set a memory interleave policy'
complete -c numactl -l weighted-interleave -s w -d 'Set a weighted memory interleave policy'
complete -c numactl -l membind -s m -d 'Only allocate memory from nodes'
complete -c numactl -l cpunodebind -s N -d 'Only execute command on the CPUs of nodes'
complete -c numactl -l physcpubind -s C -d 'Only execute process on cpus'
complete -c numactl -l localalloc -s l -d 'Try to allocate on the current node of the process, but if memory cannot be a…'
complete -c numactl -l preferred -s p -d 'Preferably allocate memory on  node, but if memory cannot be allocated there …'
complete -c numactl -l balancing -s b -d 'Enable Linux kernel NUMA balancing for the process if it is supported by kern…'
complete -c numactl -l preferred-many -s P -d 'Preferably allocate memory on nodes, but if memory cannot be allocated there …'
complete -c numactl -l show -s s -d 'Show NUMA policy settings of the current process'
complete -c numactl -l hardware -s H -d 'Show inventory of available nodes on the system.  When the'
complete -c numactl -l cpu-compress -d 'option is set show cpu ranges'
complete -c numactl -l version -d 'print the version of the numactl package and exit'
complete -c numactl -l shm
complete -c numactl -l shmid
complete -c numactl -l file -d 'to specify the shared memory segment or file and a memory policy like describ…'
complete -c numactl -l huge -d 'When creating a SYSV shared memory segment use huge pages'
complete -c numactl -l offset -d 'Specify offset into the shared memory segment.  Default 0'
complete -c numactl -l strict -d 'Give an error when a page in the policied area in the shared memory segment a…'
complete -c numactl -l shmmode -d 'Only valid before --shmid or --shm When creating a shared memory segment set …'
complete -c numactl -l length -d 'Apply policy to  length  range in the shared memory segment or make  the segm…'
complete -c numactl -l touch -d 'Touch pages to enforce policy early'
complete -c numactl -l dump -d 'Dump policy in the specified range'
complete -c numactl -l dump-nodes -d 'Dump all nodes of the specific range (very verbose!)'
complete -c numactl -l cpubind -d 'which accepts node numbers, not cpu numbers, is deprecated and replaced with …'

