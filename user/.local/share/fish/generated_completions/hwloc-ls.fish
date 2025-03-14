# hwloc-ls
# Autogenerated from man page /usr/share/man/man1/hwloc-ls.1.gz
complete -c hwloc-ls -l of -l output-format -d 'Enforce the output in the given format.  See the OUTPUT FORMATS section below'
complete -c hwloc-ls -s i -l input -d 'Read the topology from <path> instead of discovering the topology of the loca…'
complete -c hwloc-ls -l if -l input-format -d 'Enforce the input in the given format, among xml, fsroot, cpuid and synthetic'
complete -c hwloc-ls -l export-xml-flags -d 'Enforce flags when exporting to the XML format'
complete -c hwloc-ls -l export-synthetic-flags -d 'Enforce flags when exporting to the synthetic format'
complete -c hwloc-ls -s v -l verbose -d 'Include additional detail'
complete -c hwloc-ls -s q -l quiet -s s -l silent -d 'Reduce the amount of details to show'
complete -c hwloc-ls -l distances -d 'Only display distance matrices'
complete -c hwloc-ls -l distances-transform -d 'Try applying a transformation to distances structures before displaying them'
complete -c hwloc-ls -l memattrs -d 'Only display memory attributes'
complete -c hwloc-ls -l cpukinds -d 'Only display CPU kinds'
complete -c hwloc-ls -l windows-processor-groups -d 'On Windows, only show information about processor groups'
complete -c hwloc-ls -s f -l force -d 'If the destination file already exists, overwrite it'
complete -c hwloc-ls -s l -l logical -d 'Display hwloc logical indexes of all objects, with prefix "L#"'
complete -c hwloc-ls -s p -l physical -d 'Display OS/physical indexes of all objects, with prefix "P#"'
complete -c hwloc-ls -l logical-index-prefix -d 'Replace " L#" with the given prefix for logical indexes'
complete -c hwloc-ls -l os-index-prefix -d 'Replace " P#" with the given prefix for physical/OS indexes'
complete -c hwloc-ls -s c -l cpuset -d 'Display the cpuset of each object'
complete -c hwloc-ls -s C -l cpuset-only -d 'Only display the cpuset of each object; do not display anything else about th…'
complete -c hwloc-ls -l cpuset-output-format -l cof -d 'Change the format of displayed CPU set strings'
complete -c hwloc-ls -l only -d 'Only show objects of the given type in the textual output'
complete -c hwloc-ls -l filter -l filter -d 'Filter objects of type <type>, or of any type if <type> is "all"'
complete -c hwloc-ls -l ignore -d 'This is the old way to specify --filter <type>:none'
complete -c hwloc-ls -l no-smt -d 'Ignore PUs.  This is identical to --filter PU:none'
complete -c hwloc-ls -l no-caches -d 'Do not show caches.  This is identical to --filter cache:none'
complete -c hwloc-ls -l no-useless-caches -d 'This is identical to --filter cache:structure'
complete -c hwloc-ls -l no-icaches -d 'This is identical to --filter icache:none'
complete -c hwloc-ls -l disallowed -d 'Include objects disallowed by administrative limitations (e'
complete -c hwloc-ls -l allow -d 'Include objects disallowed by administrative limitations (implies --disallowe…'
complete -c hwloc-ls -l flags -d 'Enforce topology flags'
complete -c hwloc-ls -l merge -d 'Do not show levels that do not have a hierarchical impact'
complete -c hwloc-ls -l no-factorize -l no-factorize -d 'Never factorize identical objects in the graphical output'
complete -c hwloc-ls -l factorize -l factorize -d 'Factorize identical children in the graphical output (enabled by default)'
complete -c hwloc-ls -l no-collapse -d 'Do not collapse identical PCI devices'
complete -c hwloc-ls -l no-cpukinds -d 'Do not show different kinds of CPUs in the graphical output'
complete -c hwloc-ls -l restrict -d 'Restrict the topology to the given cpuset'
complete -c hwloc-ls -l restrict-flags -d 'Enforce flags when restricting the topology'
complete -c hwloc-ls -l no-io -d 'Do not show any I/O device or bridge.  This is identical to --filter io:none'
complete -c hwloc-ls -l no-bridges -d 'Do not show any I/O bridge except hostbridges'
complete -c hwloc-ls -l whole-io -d 'Show all I/O devices and bridges.  This is identical to --filter io:all'
complete -c hwloc-ls -l thissystem -d 'Assume that the selected backend provides the topology for the system on whic…'
complete -c hwloc-ls -l pid -d 'Detect topology as seen by process <pid>, i. e'
complete -c hwloc-ls -l ps -l top -d 'Show existing processes as misc objects in the output'
complete -c hwloc-ls -l misc-from -d 'Add Misc objects as described in <file> containing entries such as:      name…'
complete -c hwloc-ls -l children-order -d 'Change the order of the different kinds of children with respect to their par…'
complete -c hwloc-ls -l fontsize -d 'Set the size of text font in the graphical output.   The default is 10'
complete -c hwloc-ls -l gridsize -d 'Set the margin between elements in the graphical output.   The default is 7'
complete -c hwloc-ls -l linespacing -d 'Set the spacing between lines of text in the graphical output'
complete -c hwloc-ls -l thickness -d 'Set the thickness of lines and boxes in the graphical output'
complete -c hwloc-ls -l horiz -l horiz -d 'Force a horizontal graphical layout instead of nearly 4/3 ratio in the graphi…'
complete -c hwloc-ls -l vert -l vert -d 'Force a vertical graphical layout instead of nearly 4/3 ratio in the graphica…'
complete -c hwloc-ls -l rect -l rect -d 'Force a rectangular graphical layout with nearly 4/3 ratio in the graphical o…'
complete -c hwloc-ls -l no-text -l no-text -d 'Do not display any text in boxes in the graphical output'
complete -c hwloc-ls -l text -l text -d 'Display text in boxes in the graphical output (default)'
complete -c hwloc-ls -l no-index -l no-index -d 'Do not show object indexes in the graphical output'
complete -c hwloc-ls -l index -l index -d 'Show object indexes in the graphical output (default)'
complete -c hwloc-ls -l no-attrs -l no-attrs -d 'Do not show object attributes (such as memory size, cache size, PCI bus ID, P…'
complete -c hwloc-ls -l attrs -l attrs -d 'Show object attributes (such as memory size, cache size, PCI bus ID, PCI link…'
complete -c hwloc-ls -l no-legend -d 'Remove all text legend lines at the bottom of the graphical output'
complete -c hwloc-ls -l no-default-legend -d 'Remove default text legend lines at the bottom of the graphical output'
complete -c hwloc-ls -l append-legend -d 'Append the line of text to the bottom of the legend in the graphical output'
complete -c hwloc-ls -l grey -l greyscale -d 'Use greyscale instead of colors in the graphical output'
complete -c hwloc-ls -l palette -d 'Change the color palette'
complete -c hwloc-ls -l binding-color -d 'Do not colorize PUs and NUMA nodes according to the binding in the graphical …'
complete -c hwloc-ls -l disallowed-color -d 'Do not colorize disallowed PUs and NUMA nodes in the graphical output'
complete -c hwloc-ls -l top-color -d 'Do not colorize task objects in the graphical output when --top is given'
complete -c hwloc-ls -l version -d 'Report version and exit'
complete -c hwloc-ls -s h -l help -d 'Display help message and exit.  DESCRIPTION'
complete -c hwloc-ls -o '.<format>' -d 'If the entire filename is "-'

