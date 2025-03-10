# paru
# Autogenerated from man page /usr/share/man/man8/paru.8.gz
complete -c paru -s P -l show -d 'Printing related options'
complete -c paru -s G -l getpkgbuild -d 'Downloads PKGBUILDs from the ABS or AUR'
complete -c paru -s B -l build -d 'Build PKGBUILDs on disk'
complete -c paru -s L -l repoctl -d 'List local repos'
complete -c paru -s C -l chrootctl -d 'Interactive shell to the chroot'
complete -c paru -s R -s S -o Si -o Sl -o Ss -o Su -o Sc -o Qu -s T -d 'These operations are extended to support both AUR and repo packages'
complete -c paru -s d -l delete -d 'cleaning it'
complete -c paru -o x/--regex -d 'regardless of SearchBy'
complete -c paru -o Sss -d 'Paru will also output a verbose search result when passing two'
complete -c paru -o Ta -d 'Will filter a list of packages to ones that appear in the AUR'
complete -c paru -l gendb -d 'Generate the development package database'
complete -c paru -s c -l clean -d 'Remove unneeded dependencies'
complete -c paru -l complete -d 'Print a list of all AUR and repo packages'
complete -c paru -s s -l stats -d 'Displays information about installed packages and system health'
complete -c paru -s w -l news -d 'Print new news from the Arch Linux homepage'
complete -c paru -s o -l order -d 'Print buildorder for targets'
complete -c paru -s p -l print -d 'Prints the PKGBUILD to the terminal instead of downloading it'
complete -c paru -l comments -d 'Print the AUR comments from the PKGBUILD\'s AUR page'
complete -c paru -l ssh -d 'Clone the AUR package using SSH (e. g. : a read-write remote)'
complete -c paru -s l -l list -d 'List packages in local repos'
complete -c paru -s y -l refresh -d 'Refresh local repos'
complete -c paru -s q -l quiet -d 'Show less information'
complete -c paru -s i -l install -d 'Install a package into the chroot'
complete -c paru -s u -l sysupgrade -d 'Upgrade the chroot'
complete -c paru -l repo -d 'Assume all targets are from the repositories'
complete -c paru -s a -l aur -d 'Assume all targets are from the AUR'
complete -c paru -l pkgbuilds -d 'Assume all targets are from the PKGBUILD repositories'
complete -c paru -l mode -d 'Select what kinds of packages paru should act on'
complete -c paru -l interactive -d 'Enable interactive package selection for -S, -R, -Ss and -Qs'
complete -c paru -l aururl -d 'Set an alternative AUR URL'
complete -c paru -l aurrpcurl -d 'Set an alternative URL for the AUR /rpc endpoint'
complete -c paru -l clonedir -d 'Directory used to download and run PKGBUILDs'
complete -c paru -l makepkg -d 'The command to use for makepkg calls'
complete -c paru -l makepkgconf -d 'Specifies a makepkg. conf file to use in the chroot environment'
complete -c paru -l pacman -d 'The command to use for pacman calls'
complete -c paru -l pacman-conf -d 'The command to use for pacman-conf calls'
complete -c paru -l git -d 'The command to use for git calls'
complete -c paru -l gitflags -d 'Passes arguments to git'
complete -c paru -l gpg -d 'The command to use for gpg calls'
complete -c paru -l gpgflags -d 'Passes arguments to gpg'
complete -c paru -l fm -d 'This enables fm review mode, where PKGBUILD review is done using the file man…'
complete -c paru -l fmflags -d 'Passes arguments to file manager'
complete -c paru -l asp -d 'The command to use for asp calls'
complete -c paru -l mflags -d 'Passes arguments to makepkg'
complete -c paru -l bat -d 'The command to use for bat calls'
complete -c paru -l batflags -d 'Passes arguments to bat'
complete -c paru -l sudo -d 'The command to use for sudo calls'
complete -c paru -l sudoflags -d 'Passes arguments to sudo'
complete -c paru -l chrootflags -d 'Passes arguments to makechrootpkg'
complete -c paru -l completioninterval -d 'Time in days to refresh the completion cache'
complete -c paru -l sortby -d 'Sort AUR results by a specific field during search.  Defaults to votes'
complete -c paru -l searchby -d 'Search for AUR packages by querying the specified field'
complete -c paru -l skipreview -d 'Skip the review process'
complete -c paru -l review -d 'Don\'t skip the review process'
complete -c paru -l upgrademenu -d 'Show a detailed list of updates in a similar format to pacman\'s VerbosePkgLis…'
complete -c paru -l noupgrademenu -d 'Do not show the upgrade menu'
complete -c paru -l removemake -d 'Remove makedepends after installing packages'
complete -c paru -l noremovemake -d 'Don\'t remove makedepends after installing packages'
complete -c paru -l topdown -d 'Print search results from top to bottom.  Repo packages will print first'
complete -c paru -l bottomup -d 'Print search results from bottom to top.  AUR packages will print first'
complete -c paru -l limit -d 'Limit the number of packages returned in a search to the given amount'
complete -c paru -s x -l regex -d 'Enable regex for aur search'
complete -c paru -l nocheck -d 'Don\'t resolve checkdepends or run the check function'
complete -c paru -l installdebug -d 'Also install debug packages when a package provides them'
complete -c paru -l noinstalldebug -d 'Don\'t install debug packages when a package provides them'
complete -c paru -l devel -d 'During sysupgrade also check AUR development packages for updates'
complete -c paru -l ignoredevel -d 'Like --ignore but for devel upgrades'
complete -c paru -l nodevel -d 'Do not check for development packages updates during sysupgrade'
complete -c paru -l develsuffixes -d 'Suffixes that paru will use to decide if a package is a devel package'
complete -c paru -l cleanafter -d 'Remove untracked files after installation'
complete -c paru -l nocleanafter -d 'Do not remove package sources after successful install'
complete -c paru -l redownload -d 'Always download PKGBUILDs of targets even when a copy is available in cache'
complete -c paru -l noredownload -d 'When downloading PKGBUILDs, if the PKGBUILD is found in cache and is equal or…'
complete -c paru -l provides -d 'Look for matching providers when searching for AUR packages'
complete -c paru -l noprovides -d 'Do not look for matching providers when searching for AUR packages'
complete -c paru -l pgpfetch -d 'Prompt to import unknown PGP keys from the validpgpkeys field of each PKGBUILD'
complete -c paru -l nopgpfetch -d 'Do not prompt to import unknown PGP keys'
complete -c paru -l newsonupgrade -d 'Print new news during sysupgrade'
complete -c paru -l useask -d 'Use pacman\'s --ask flag to automatically confirm package conflicts'
complete -c paru -l nouseask -d 'Manually resolve package conflicts during the install'
complete -c paru -l savechanges -d 'Commit changes to pkgbuilds made during review'
complete -c paru -l nosavechanges -d 'Don\'t commit changes to pkgbuilds made during review'
complete -c paru -l failfast -d 'Exit as soon as any AUR packages fail to build'
complete -c paru -l nofailfast -d 'Don\'t exit as soon as any AUR packages fail to build'
complete -c paru -l keepsrc -d 'Keep src/ and pkg/ directories after building packages'
complete -c paru -l nokeepsrc -d 'Don\'t keep src/ and pkg/ directories after building packages'
complete -c paru -l combinedupgrade -d 'During sysupgrade, paru will first perform a refresh, then show its combined …'
complete -c paru -l nocombinedupgrade -d 'During sysupgrade, pacman -Syu will be called, then the AUR upgrade will start'
complete -c paru -l batchinstall -d 'When building and installing AUR packages instead of installing each package …'
complete -c paru -l nobatchinstall -d 'Always install AUR packages immediately after building them'
complete -c paru -l rebuild -d 'Always build target packages even when a copy is available in cache'
complete -c paru -l norebuild -d 'When building packages if the package is found in cache and is an equal versi…'
complete -c paru -l sudoloop -d 'Periodically call sudo in the background to prevent it from timing out during…'
complete -c paru -l nosudoloop -d 'Do not loop sudo calls in the background'
complete -c paru -l localrepo -d 'Use a local repo to build and upgrade AUR packages'
complete -c paru -l nolocalrepo -d 'Do not build into a local repo'
complete -c paru -l chroot -d 'Build packages in a chroot.  This requires the LocalRepo option to be enabled'
complete -c paru -l nochroot -d 'Don\'t build packages in a chroot'
complete -c paru -l sign -d 'Sign packages with gpg.  Optionally indicate which key to sign with'
complete -c paru -l nosign -d 'Don\'t sign package with gpg'
complete -c paru -l keeprepocache -d 'Normally upon AUR packages getting updated the old versions will be removed f…'
complete -c paru -l nokeeprepocache -d 'Don\'t keep old packages'
complete -c paru -l signdb -d 'Sign databases with gpg.  Optionally indicate which key to sign with'
complete -c paru -l nosigndb -d 'Don\'t sign databases with gpg'

