# gpg
# Autogenerated from man page /usr/share/man/man1/gpg.1.gz
complete -c gpg -l default-key -d 'Use name as the default key to sign with'
complete -c gpg -l default-recipient -d 'Use name as default recipient if option --recipient is not used and don\'t ask…'
complete -c gpg -l default-recipient-self -d 'Use the default key as default recipient if option --recipient is not used an…'
complete -c gpg -l no-default-recipient -d 'Reset --default-recipient and --default-recipient-self'
complete -c gpg -s v -l verbose -d 'Give more information during processing'
complete -c gpg -l no-verbose -d 'Reset verbose level to 0.   Should not be used in an option file'
complete -c gpg -s q -l quiet -d 'Try to be as quiet as possible.   Should not be used in an option file'
complete -c gpg -l batch -d 'TQ   --no-batch Use batch mode'
complete -c gpg -l no-tty -d 'Make sure that the TTY (terminal) is never used for any output'
complete -c gpg -l yes -d 'Assume "yes" on most questions.   Should not be used in an option file'
complete -c gpg -l no -d 'Assume "no" on most questions.   Should not be used in an option file'
complete -c gpg -l proc-all-sigs -d 'This option overrides the behaviour of the --batch option to stop signature v…'
complete -c gpg -l list-filter -d 'A list filter can be used to output only certain keys during key listing comm…'
complete -c gpg -l list-options -d 'This is a space or comma delimited string that gives options used when listin…'
complete -c gpg -l verify-options -d 'This is a space or comma delimited string that gives options used when verify…'
complete -c gpg -l enable-large-rsa -d 'TQ   --disable-large-rsa With --generate-key and --batch, enable the creation…'
complete -c gpg -l enable-dsa2 -d 'TQ   --disable-dsa2 Enable hash truncation for all DSA keys even for old DSA …'
complete -c gpg -l photo-viewer -d 'This is the command line that should be run to view a photo ID'
complete -c gpg -l exec-path -d 'Sets a list of directories to search for photo viewers If not provided photo …'
complete -c gpg -l keyring -d 'Add file to the current list of keyrings'
complete -c gpg -l primary-keyring -d 'This is a varian of --keyring and designates file as the primary public keyri…'
complete -c gpg -l secret-keyring -d 'This is an obsolete option and ignored'
complete -c gpg -l trustdb-name -d 'Use file instead of the default trustdb'
complete -c gpg -l homedir -d 'Set the name of the home directory to dir'
complete -c gpg -l display-charset -d 'Set the name of the native character set'
complete -c gpg -l utf8-strings -d 'TQ   --no-utf8-strings Assume that command line arguments are given as UTF-8 …'
complete -c gpg -l options -d 'Read options from file and do not try to read them from the default options f…'
complete -c gpg -l no-options -d 'Shortcut for --options /dev/null'
complete -c gpg -s z -d 'TQ   --compress-level n . TQ   --bzip2-compress-level n '
complete -c gpg -l bzip2-decompress-lowmem -d 'Use a different decompression method for BZIP2 compressed files'
complete -c gpg -l mangle-dos-filenames -d 'TQ   --no-mangle-dos-filenames Older version of Windows cannot handle filenam…'
complete -c gpg -l ask-cert-level -d 'TQ   --no-ask-cert-level When making a key signature, prompt for a certificat…'
complete -c gpg -l default-cert-level -d 'The default to use for the check level when signing a key'
complete -c gpg -l min-cert-level -d 'When building the trust database, treat any signatures with a certification l…'
complete -c gpg -l trusted-key -d 'Assume that the specified key (which should be given as fingerprint) is as tr…'
complete -c gpg -l add-desig-revoker -d 'Add the key specified by fingerprint as a designated revoker to newly created…'
complete -c gpg -l default-new-key-adsk -d 'Add the subkey specified by fingerprint as an Additional Decryption Subkey (A…'
complete -c gpg -l trust-model -d 'Set what trust model GnuPG should follow.  The models are:  . RS'
complete -c gpg -l always-trust -d 'Identical to --trust-model always'
complete -c gpg -l assert-signer -d 'This option checks whether at least one valid signature on a file has been ma…'
complete -c gpg -l assert-pubkey-algo -d 'During data signature verification this options checks whether the used publi…'
complete -c gpg -l auto-key-locate -d 'TQ   --no-auto-key-locate GnuPG can automatically locate and retrieve keys as…'
complete -c gpg -l auto-key-import -d 'TQ   --no-auto-key-import This is an offline mechanism to get a missing key f…'
complete -c gpg -l auto-key-retrieve -d 'TQ   --no-auto-key-retrieve These options enable or disable the automatic ret…'
complete -c gpg -l keyid-format -d 'Select how to display key IDs'
complete -c gpg -l keyserver -d 'This option is deprecated - please use the --keyserver in \'dirmngr'
complete -c gpg -l keyserver-options -d 'This is a space or comma delimited string that gives options for the keyserver'
complete -c gpg -l completes-needed -d 'Number of completely trusted users to introduce a new key signer (defaults to…'
complete -c gpg -l marginals-needed -d 'Number of marginally trusted users to introduce a new key signer (defaults to…'
complete -c gpg -l tofu-default-policy -d 'The default TOFU policy (defaults to auto)'
complete -c gpg -l max-cert-depth -d 'Maximum depth of a certification chain (default is 5)'
complete -c gpg -l no-sig-cache -d 'Do not cache the verification status of key signatures'
complete -c gpg -l auto-check-trustdb -d 'TQ   --no-auto-check-trustdb If GnuPG feels that its information about the We…'
complete -c gpg -l use-agent -d 'TQ   --no-use-agent This is dummy option.  gpg always requires the agent'
complete -c gpg -l gpg-agent-info -d 'This is dummy option.  It has no effect when used with gpg'
complete -c gpg -l agent-program -d 'Specify an agent program to be used for secret key operations'
complete -c gpg -l dirmngr-program -d 'Specify a dirmngr program to be used for keyserver access'
complete -c gpg -l disable-dirmngr -d 'Entirely disable the use of the Dirmngr'
complete -c gpg -l no-autostart -d 'Do not start the gpg-agent or the dirmngr if it has not yet been started and …'
complete -c gpg -l lock-once -d 'Lock the databases the first time a lock is requested and do not release the …'
complete -c gpg -l lock-multiple -d 'Release the locks every time a lock is no longer needed'
complete -c gpg -l lock-never -d 'Disable locking entirely'
complete -c gpg -l exit-on-status-write-error -d 'This option will cause write errors on the status FD to immediately terminate…'
complete -c gpg -l limit-card-insert-tries -d 'With n greater than 0 the number of prompts asking to insert a smartcard gets…'
complete -c gpg -l no-random-seed-file -d 'GnuPG uses a file to store its internal random pool over invocations'
complete -c gpg -l no-greeting -d 'Suppress the initial copyright message'
complete -c gpg -l no-secmem-warning -d 'Suppress the warning about "using insecure memory"'
complete -c gpg -l no-permission-warning -d 'Suppress the warning about unsafe file and home directory (--homedir) permiss…'
complete -c gpg -l require-secmem -d 'TQ   --no-require-secmem Refuse to run if GnuPG cannot get secure memory'
complete -c gpg -l require-cross-certification -d 'TQ   --no-require-cross-certification When verifying a signature made from a …'
complete -c gpg -l expert -d 'TQ   --no-expert Allow the user to do certain nonsensical or "silly" things l…'
complete -c gpg -l recipient -d 'TQ   -r Encrypt for user id name'
complete -c gpg -l hidden-recipient -d 'TQ   -R Encrypt for user ID name, but hide the key ID of this user\'s key'
complete -c gpg -l recipient-file -d 'TQ   -f This option is similar to --recipient except that it encrypts to a ke…'
complete -c gpg -l hidden-recipient-file -d 'TQ   -F This option is similar to --hidden-recipient except that it encrypts …'
complete -c gpg -l encrypt-to -d 'Same as --recipient but this one is intended for use in the options file and …'
complete -c gpg -l hidden-encrypt-to -d 'Same as --hidden-recipient but this one is intended for use in the options fi…'
complete -c gpg -l no-encrypt-to -d 'Disable the use of all --encrypt-to and --hidden-encrypt-to keys'
complete -c gpg -l group -d 'Sets up a named group, which is similar to aliases in email programs'
complete -c gpg -l ungroup -d 'Remove a given entry from the --group list'
complete -c gpg -l no-groups -d 'Remove all entries from the --group list'
complete -c gpg -l local-user -d 'TQ   -u Use name as the key to sign with'
complete -c gpg -l sender -d 'This option has two purposes'
complete -c gpg -l try-secret-key -d 'For hidden recipients GPG needs to know the keys to use for trial decryption'
complete -c gpg -l try-all-secrets -d 'Don\'t look at the key ID as stored in the message but try all secret keys in …'
complete -c gpg -l skip-hidden-recipients -d 'TQ   --no-skip-hidden-recipients During decryption skip all anonymous recipie…'
complete -c gpg -l armor -d 'TQ   -a Create ASCII armored output'
complete -c gpg -l no-armor -d 'Assume the input data is not in ASCII armored format'
complete -c gpg -l output -d 'TQ   -o file Write output to file.   To write to stdout use - as the filename'
complete -c gpg -l max-output -d 'This option sets a limit on the number of bytes that will be generated when p…'
complete -c gpg -l chunk-size -d 'The AEAD encryption mode encrypts the data in chunks so that a receiving side…'
complete -c gpg -l input-size-hint -d 'This option can be used to tell GPG the size of the input data in bytes'
complete -c gpg -l key-origin -d 'gpg can track the origin of a key.  Certain origins are implicitly known (e'
complete -c gpg -l import-options -d 'This is a space or comma delimited string that gives options for importing ke…'
complete -c gpg -l import-filter -d 'TQ   --export-filter {name=expr} These options define an import/export filter…'
complete -c gpg -l export-options -d 'This is a space or comma delimited string that gives options for exporting ke…'
complete -c gpg -l with-colons -d 'Print key listings delimited by colons'
complete -c gpg -l fixed-list-mode -d 'Do not merge primary user ID and primary key in --with-colon listing mode and…'
complete -c gpg -l legacy-list-mode -d 'Revert to the pre-2. 1 public key list mode'
complete -c gpg -l with-fingerprint -d 'Same as the command --fingerprint but changes only the format of the output a…'
complete -c gpg -l with-subkey-fingerprint -d 'If a fingerprint is printed for the primary key, this option forces printing …'
complete -c gpg -l with-v5-fingerprint -d 'In a colon mode listing emit "fp2" lines for version 4 OpenPGP keys having a …'
complete -c gpg -l with-icao-spelling -d 'Print the ICAO spelling of the fingerprint in addition to the hex digits'
complete -c gpg -l with-keygrip -d 'Include the keygrip in the key listings'
complete -c gpg -l with-key-origin -d 'Include the locally held information on the origin and last update of a key i…'
complete -c gpg -l with-wkd-hash -d 'Print a Web Key Directory identifier along with each user ID in key listings'
complete -c gpg -l with-secret -d 'Include info about the presence of a secret key in public key listings done w…'
complete -c gpg -l force-ocb -d 'TQ   --force-aead Force the use of AEAD encryption over MDC encryption'
complete -c gpg -l force-mdc -d 'TQ   --disable-mdc These options are obsolete and have no effect since GnuPG 2'
complete -c gpg -l disable-signer-uid -d 'By default the user ID of the signing key is embedded in the data signature'
complete -c gpg -l include-key-block -d 'TQ   --no-include-key-block This option is used to embed the actual signing k…'
complete -c gpg -l personal-cipher-preferences -d 'Set the list of personal cipher preferences to string'
complete -c gpg -l personal-digest-preferences -d 'Set the list of personal digest preferences to string'
complete -c gpg -l personal-compress-preferences -d 'Set the list of personal compression preferences to string'
complete -c gpg -l s2k-cipher-algo -d 'Use name as the cipher algorithm for symmetric encryption with a passphrase i…'
complete -c gpg -l s2k-digest-algo -d 'Use name as the digest algorithm used to mangle the passphrases for symmetric…'
complete -c gpg -l s2k-mode -d 'Selects how passphrases for symmetric encryption are mangled'
complete -c gpg -l s2k-count -d 'Specify how many times the passphrases mangling for symmetric encryption is r…'
complete -c gpg -l gnupg -d 'Use standard GnuPG behavior'
complete -c gpg -l openpgp -d 'Reset all packet, cipher and digest options to strict OpenPGP behavior'
complete -c gpg -l rfc4880 -d 'Reset all packet, cipher and digest options to strict RFC-4880 behavior'
complete -c gpg -l rfc4880bis -d 'Reset all packet, cipher and digest options to strict according to the propos…'
complete -c gpg -l rfc2440 -d 'Reset all packet, cipher and digest options to strict RFC-2440 behavior'
complete -c gpg -l pgp6 -d 'This option is obsolete; it is handled as an alias for --pgp7'
complete -c gpg -l pgp7 -d 'Set up all options to be as PGP 7 compliant as possible'
complete -c gpg -l pgp8 -d 'Set up all options to be as PGP 8 compliant as possible'
complete -c gpg -l compliance -d 'This option can be used instead of one of the options above'
complete -c gpg -l min-rsa-length -d 'This option adjusts the compliance mode "de-vs" for stricter key size require…'
complete -c gpg -l require-compliance -d 'To check that data has been encrypted according to the rules of the current c…'
complete -c gpg -s n -d 'TQ   --dry-run Don\'t make any changes (this is not completely implemented)'
complete -c gpg -l list-only -d 'Changes the behaviour of some commands'
complete -c gpg -s i -d 'TQ   --interactive Prompt before overwriting any files'
complete -c gpg -l compatibility-flags -d 'Set compatibility flags to work around problems due to non-compliant keys or …'
complete -c gpg -l debug-level -d 'Select the debug level for investigating problems'
complete -c gpg -l debug -d 'Set debug flags.   All flags are or-ed and flags may be given in C syntax (e'
complete -c gpg -l debug-all -d 'Set all useful debugging flags'
complete -c gpg -l debug-iolbf -d 'Set stdout into line buffered mode'
complete -c gpg -l debug-set-iobuf-size -d 'Change the buffer size of the IOBUFs to n kilobyte'
complete -c gpg -l debug-allow-large-chunks -d 'To facilitate software tests and experiments this option allows one to specif…'
complete -c gpg -l debug-ignore-expiration -d 'This option tries to override certain key expiration dates'
complete -c gpg -l faked-system-time -d 'This option is only useful for testing; it sets the system time back or forth…'
complete -c gpg -l full-timestrings -d 'Change the format of printed creation and expiration times from just the date…'
complete -c gpg -l enable-progress-filter -d 'Enable certain PROGRESS status outputs'
complete -c gpg -l status-fd -d 'Write special status strings to the file descriptor n'
complete -c gpg -l status-file -d 'Same as --status-fd, except the status data is written to file file'
complete -c gpg -l logger-fd -d 'Write log output to file descriptor n and not to STDERR'
complete -c gpg -l log-file -d 'TQ   --logger-file file Same as --logger-fd, except the logger data is writte…'
complete -c gpg -l log-time -d 'Prefix all log output with a timestamp even if no log file is used'
complete -c gpg -l attribute-fd -d 'Write attribute subpackets to the file descriptor n'
complete -c gpg -l attribute-file -d 'Same as --attribute-fd, except the attribute data is written to file file'
complete -c gpg -l comment -d 'TQ   --no-comments Use string as a comment string in cleartext signatures and…'
complete -c gpg -l emit-version -d 'TQ   --no-emit-version Force inclusion of the version string in ASCII armored…'
complete -c gpg -l sig-notation -d 'TQ   --cert-notation {name=value} '
complete -c gpg -l known-notation -d 'Adds name to a list of known critical signature notations'
complete -c gpg -l sig-policy-url -d 'TQ   --cert-policy-url string '
complete -c gpg -l sig-keyserver-url -d 'Use string as a preferred keyserver URL for data signatures'
complete -c gpg -l set-filename -d 'Use string as the filename which is stored inside messages'
complete -c gpg -l for-your-eyes-only -d 'TQ   --no-for-your-eyes-only Set the `for your eyes only\' flag in the message'
complete -c gpg -l use-embedded-filename -d 'TQ   --no-use-embedded-filename Try to create a file with a name as embedded …'
complete -c gpg -l cipher-algo -d 'Use name as cipher algorithm'
complete -c gpg -l digest-algo -d 'Use name as the message digest algorithm'
complete -c gpg -l compress-algo -d 'Use compression algorithm name.  "zlib" is RFC-1950 ZLIB compression'
complete -c gpg -l cert-digest-algo -d 'Use name as the message digest algorithm used when signing a key'
complete -c gpg -l disable-cipher-algo -d 'Never allow the use of name as cipher algorithm'
complete -c gpg -l disable-pubkey-algo -d 'Never allow the use of name as public key algorithm'
complete -c gpg -l throw-keyids -d 'TQ   --no-throw-keyids Do not put the recipient key IDs into encrypted messag…'
complete -c gpg -l not-dash-escaped -d 'This option changes the behavior of cleartext signatures so that they can be …'
complete -c gpg -l escape-from-lines -d 'TQ   --no-escape-from-lines Because some mailers change lines starting with "…'
complete -c gpg -l passphrase-repeat -d 'Specify how many times gpg will request a new passphrase be repeated'
complete -c gpg -l passphrase-fd -d 'Read the passphrase from file descriptor n'
complete -c gpg -l passphrase-file -d 'Read the passphrase from file file'
complete -c gpg -l passphrase -d 'Use string as the passphrase'
complete -c gpg -l pinentry-mode -d 'Set the pinentry mode to mode.   Allowed values for mode are: . RS'
complete -c gpg -l no-symkey-cache -d 'Disable the passphrase cache used for symmetrical en- and decryption'
complete -c gpg -l request-origin -d 'Tell gpg to assume that the operation ultimately originated at origin'
complete -c gpg -l command-fd -d 'This is a replacement for the deprecated shared-memory IPC mode'
complete -c gpg -l command-file -d 'Same as --command-fd, except the commands are read out of file file'
complete -c gpg -l allow-non-selfsigned-uid -d 'TQ   --no-allow-non-selfsigned-uid Allow the import and use of keys with user…'
complete -c gpg -l allow-freeform-uid -d 'Disable all checks on the form of the user ID while generating a new one'
complete -c gpg -l ignore-time-conflict -d 'GnuPG normally checks that the timestamps associated with keys and signatures…'
complete -c gpg -l ignore-valid-from -d 'GnuPG normally does not select and use subkeys created in the future'
complete -c gpg -l ignore-crc-error -d 'The ASCII armor used by OpenPGP is protected by a CRC checksum against transm…'
complete -c gpg -l ignore-mdc-error -d 'This option changes a MDC integrity protection failure into a warning'
complete -c gpg -l allow-old-cipher-algos -d 'Old cipher algorithms like 3DES, IDEA, or CAST5 encrypt data using blocks of …'
complete -c gpg -l allow-weak-digest-algos -d 'Signatures made with known-weak digest algorithms are normally rejected with …'
complete -c gpg -l weak-digest -d 'Treat the specified digest algorithm as weak'
complete -c gpg -l allow-weak-key-signatures -d 'To avoid a minor risk of collision attacks on third-party key signatures made…'
complete -c gpg -l override-compliance-check -d 'This was a temporary introduced option and has no more effect'
complete -c gpg -l no-default-keyring -d 'Do not add the default keyring to the list of keyrings'
complete -c gpg -l no-keyring -d 'Do not use any keyring at all'
complete -c gpg -l skip-verify -d 'Skip the signature verification step'
complete -c gpg -l with-key-data -d 'Print key listings delimited by colons (like --with-colons) and print the pub…'
complete -c gpg -l list-signatures -d 'TQ   --list-sigs Same as --list-keys, but the signatures are listed too'
complete -c gpg -l fast-list-mode -d 'Changes the output of the list commands to work faster; this is achieved by l…'
complete -c gpg -l no-literal -d 'This is not for normal use'
complete -c gpg -l set-filesize -d 'This is not for normal use'
complete -c gpg -l show-session-key -d 'Display the session key used for one message'
complete -c gpg -l override-session-key -d 'TQ   --override-session-key-fd fd Don\'t use the public key but the session ke…'
complete -c gpg -l ask-sig-expire -d 'TQ   --no-ask-sig-expire When making a data signature, prompt for an expirati…'
complete -c gpg -l default-sig-expire -d 'The default expiration time to use for signature expiration'
complete -c gpg -l ask-cert-expire -d 'TQ   --no-ask-cert-expire When making a key signature, prompt for an expirati…'
complete -c gpg -l default-cert-expire -d 'The default expiration time to use for key signature expiration'
complete -c gpg -l default-new-key-algo -d 'This option can be used to change the default algorithms for key generation'
complete -c gpg -l no-auto-trust-new-key -d 'When creating a new key the ownertrust of the new key is set to ultimate'
complete -c gpg -l force-sign-key -d 'This option modifies the behaviour of the commands --quick-sign-key, --quick-…'
complete -c gpg -l forbid-gen-key -d 'This option is intended for use in the global config file to disallow the use…'
complete -c gpg -l allow-secret-key-import -d 'This is an obsolete option and is not used anywhere'
complete -c gpg -l no-allow-multiple-messages -d 'These are obsolete options; they have no more effect since GnuPG 2. 2. 8'
complete -c gpg -l enable-special-filenames -d 'This option enables a mode in which filenames of the form \'-&n\', where n is a…'
complete -c gpg -l no-expensive-trust-checks -d 'Experimental use only'
complete -c gpg -l preserve-permissions -d 'Don\'t change the permissions of a secret keyring back to user read/write only'
complete -c gpg -l default-preference-list -d 'Set the list of default preferences to string'
complete -c gpg -l default-keyserver-url -d 'Set the default keyserver URL to name'
complete -c gpg -l list-config -d 'Display various internal configuration parameters of GnuPG'
complete -c gpg -l list-gcrypt-config -d 'Display various internal configuration parameters of Libgcrypt'
complete -c gpg -l gpgconf-list -d 'This command is similar to --list-config but in general only internally used …'
complete -c gpg -l gpgconf-test -d 'This is more or less dummy action'
complete -c gpg -l chuid -d 'Change the current user to uid which may either be a number or a name'
complete -c gpg -s t -l textmode -d 'TQ   --no-textmode Treat input files as text and store them in the OpenPGP ca…'
complete -c gpg -l force-v3-sigs -d 'TQ   --no-force-v3-sigs'
complete -c gpg -l force-v4-certs -d 'TQ   --no-force-v4-certs These options are obsolete and have no effect since …'
complete -c gpg -l show-photos -d 'TQ   --no-show-photos Causes --list-keys, --list-signatures, --list-public-ke…'
complete -c gpg -l show-keyring -d 'Display the keyring name at the head of key listings to show which keyring a …'
complete -c gpg -l show-notation -d 'TQ   --no-show-notation Show signature notations in the --list-signatures or …'
complete -c gpg -l show-policy-url -d 'TQ   --no-show-policy-url Show policy URLs in the --list-signatures or --chec…'
complete -c gpg -l personal-aead-preferences -d 'This option is deprecated and has no more effect since version 2. 3. 9'
complete -c gpg -l version -d 'Print the program version and licensing information'
complete -c gpg -l help
complete -c gpg -s h -d 'Print a usage message summarizing the most useful command-line options'
complete -c gpg -l warranty -d 'Print warranty information'
complete -c gpg -l dump-options -d 'Print a list of all available options and commands'
complete -c gpg -l sign
complete -c gpg -s s -d 'Sign a message'
complete -c gpg -l symmetric -d 'decrypted using a secret key or a passphrase)'
complete -c gpg -l clear-sign
complete -c gpg -l clearsign -d 'Make a cleartext signature'
complete -c gpg -l detach-sign
complete -c gpg -s b -d 'Make a detached signature'
complete -c gpg -l encrypt
complete -c gpg -s e -d 'Encrypt data to one or more public keys'
complete -c gpg -s c -d 'Encrypt with a symmetric cipher using a passphrase'
complete -c gpg -l store -d 'Store only (make a simple literal data packet)'
complete -c gpg -l decrypt
complete -c gpg -s d -d 'Decrypt the file given on the command line (or STDIN if no file is specified)…'
complete -c gpg -l verify -d 'Assume that the first argument is a signed file and verify it without generat…'
complete -c gpg -l multifile -d 'This modifies certain other commands to accept multiple files for processing …'
complete -c gpg -l verify-files -d 'Identical to --multifile --verify'
complete -c gpg -l encrypt-files -d 'Identical to --multifile --encrypt'
complete -c gpg -l decrypt-files -d 'Identical to --multifile --decrypt'
complete -c gpg -l list-keys
complete -c gpg -s k
complete -c gpg -l list-public-keys -d 'List the specified keys'
complete -c gpg -l list-secret-keys
complete -c gpg -s K -d 'List the specified secret keys'
complete -c gpg -l check-signatures
complete -c gpg -l check-sigs -d 'Same as --list-keys, but the key signatures are verified and listed too'
complete -c gpg -l locate-keys
complete -c gpg -l locate-external-keys -d 'Locate the keys given as arguments'
complete -c gpg -l show-keys -d 'This commands takes OpenPGP keys as input and prints information about them i…'
complete -c gpg -l fingerprint -d 'List all keys (or the specified ones) along with their fingerprints'
complete -c gpg -l list-packets -d 'List only the sequence of packets'
complete -c gpg -l edit-card
complete -c gpg -l card-edit -d 'Present a menu to work with a smartcard'
complete -c gpg -l card-status -d 'Show the content of the smart card'
complete -c gpg -l change-pin -d 'Present a menu to allow changing the PIN of a smartcard'
complete -c gpg -l delete-keys -d 'Remove key from the public keyring'
complete -c gpg -l delete-secret-keys -d 'Remove key from the secret keyring'
complete -c gpg -l delete-secret-and-public-key -d 'Same as --delete-key, but if a secret key exists, it will be removed first'
complete -c gpg -l export -d 'Either export all keys from all keyrings (default keyring and those registere…'
complete -c gpg -l send-keys -d 'Similar to --export but sends the keys to a keyserver'
complete -c gpg -l export-secret-keys
complete -c gpg -l export-secret-subkeys -d 'Same as --export, but exports the secret keys instead'
complete -c gpg -l export-ssh-key -d 'This command is used to export a key in the OpenSSH public key format'
complete -c gpg -l import
complete -c gpg -l fast-import -d 'Import/merge keys.  This adds the given keys to the keyring'
complete -c gpg -l receive-keys
complete -c gpg -l recv-keys -d 'Import the keys with the given keyIDs from a keyserver'
complete -c gpg -l refresh-keys -d 'Request updates from a keyserver for keys that already exist on the local key…'
complete -c gpg -l search-keys -d 'Search the keyserver for the given names'
complete -c gpg -l fetch-keys -d 'Retrieve keys located at the specified URIs'
complete -c gpg -l update-trustdb -d 'Do trust database maintenance'
complete -c gpg -l edit-key
complete -c gpg -l check-trustdb -d 'Do trust database maintenance without user interaction'
complete -c gpg -l export-ownertrust -d 'Send the ownertrust values to STDOUT'
complete -c gpg -l import-ownertrust -d 'Update the trustdb with the ownertrust values stored in files (or STDIN if no…'
complete -c gpg -l rebuild-keydb-caches -d 'When updating from version 1. 0. 6 to 1. 0'
complete -c gpg -l print-md
complete -c gpg -l print-mds -d 'Print message digest of algorithm algo for all given files or STDIN'
complete -c gpg -l gen-random -d 'Emit count random bytes of the given quality level 0, 1 or 2'
complete -c gpg -l gen-prime -d 'Use the source, Luke :-)'
complete -c gpg -l enarmor
complete -c gpg -l dearmor -d 'Pack or unpack an arbitrary input into/from an OpenPGP ASCII armor'
complete -c gpg -l unwrap -d 'This option modifies the command --decrypt to output the original message wit…'
complete -c gpg -l tofu-policy -d 'Set the TOFU policy for all the bindings associated with the specified keys'
complete -c gpg -l quick-generate-key
complete -c gpg -l quick-gen-key -d 'This is a simple command to generate a standard key with one user id'
complete -c gpg -l quick-add-key -d '``cert\'\' which can be used to create a certification only primary key; the de…'
complete -c gpg -l quick-set-expire -d 'With two arguments given, directly set the expiration time of the primary key…'
complete -c gpg -l quick-add-adsk -d 'Directly add an Additional Decryption Subkey to the key identified by the fin…'
complete -c gpg -l generate-key
complete -c gpg -l gen-key -d 'Generate a new key pair using the current default parameters'
complete -c gpg -l full-generate-key
complete -c gpg -l full-gen-key -d 'Generate a new key pair with dialogs for all options'
complete -c gpg -l generate-revocation
complete -c gpg -l gen-revoke -d 'Generate a revocation certificate for the complete key'
complete -c gpg -l generate-designated-revocation
complete -c gpg -l desig-revoke -d 'Generate a designated revocation certificate for a key'
complete -c gpg -s u -d 'lsign Same as "sign" but the signature is marked as non-exportable and will t…'
complete -c gpg -l cert-notation -d '"none" removes all notations, setting a notation prefixed with a minus sign (…'
complete -c gpg -l sign-key -d 'Signs a public key with your secret key'
complete -c gpg -l lsign-key -d 'Signs a public key with your secret key but marks it as non-exportable'
complete -c gpg -l quick-sign-key
complete -c gpg -l quick-lsign-key -d 'Directly sign a key from the passphrase without any further user interaction'
complete -c gpg -l quick-add-uid -d 'This command adds a new user id to an existing key'
complete -c gpg -l quick-revoke-uid -d 'This command revokes a user ID on an existing key'
complete -c gpg -l quick-revoke-sig -d 'This command revokes the key signatures made by signing-fpr from the key spec…'
complete -c gpg -l quick-set-primary-uid -d 'This command sets or updates the primary user ID flag on an existing key'
complete -c gpg -l quick-update-pref -d 'This command updates the preference list of the key to the current default va…'
complete -c gpg -l quick-set-ownertrust -d 'This command sets the ownertrust of a key and can also be used to set the dis…'
complete -c gpg -l change-passphrase
complete -c gpg -l passwd -d 'Change the passphrase of the secret key belonging to the certificate specifie…'
complete -c gpg -l no-batch -d 'Use batch mode.   Never ask, do not allow interactive commands'
complete -c gpg -l disable-large-rsa -d 'With --generate-key and --batch, enable the creation of RSA secret keys as la…'
complete -c gpg -l disable-dsa2 -d 'Enable hash truncation for all DSA keys even for old DSA Keys up to 1024 bit'
complete -c gpg -l recv-from -d keyring
complete -c gpg -l no-utf8-strings -d 'Assume that command line arguments are given as UTF-8 strings'
complete -c gpg -l compress-level
complete -c gpg -l bzip2-compress-level
complete -c gpg -l no-compress -d 'Set compression level to n for the ZIP and ZLIB compression algorithms'
complete -c gpg -l 'no-compress;' -o z-1 -d 'option z with another compression level than the default as indicated by -1'
complete -c gpg -l no-mangle-dos-filenames -d 'Older version of Windows cannot handle filenames with more than one dot'
complete -c gpg -l no-ask-cert-level -d 'When making a key signature, prompt for a certification level'
complete -c gpg -l no-auto-key-locate -d 'GnuPG can automatically locate and retrieve keys as needed using this option'
complete -c gpg -l locate-external-key -d 'actually a shortcut for the mechanism `ldap\' using only "ldap:///" as the key…'
complete -c gpg -l no-auto-key-import -d 'This is an offline mechanism to get a missing key for signature verification …'
complete -c gpg -l no-auto-key-retrieve -d 'These options enable or disable the automatic retrieving of keys from a keyse…'
complete -c gpg -l no-auto-check-trustdb -d 'If GnuPG feels that its information about the Web of Trust has to be updated,…'
complete -c gpg -l no-use-agent -d 'This is dummy option.  gpg always requires the agent'
complete -c gpg -l no-require-secmem -d 'Refuse to run if GnuPG cannot get secure memory.  Defaults to no (i. e'
complete -c gpg -l no-require-cross-certification -d 'When verifying a signature made from a subkey, ensure that the cross certific…'
complete -c gpg -l no-expert -d 'Allow the user to do certain nonsensical or "silly" things like signing an ex…'
complete -c gpg -s r -d 'Encrypt for user id name.  If this option or'
complete -c gpg -s R -d 'Encrypt for user ID name, but hide the key ID of this user\'s key'
complete -c gpg -s f -d 'This option is similar to --recipient except that it encrypts to a key stored…'
complete -c gpg -s F -d 'This option is similar to --hidden-recipient except that it encrypts to a key…'
complete -c gpg -l - -d 'from the command line, it may be necessary to quote the argument to this opti…'
complete -c gpg -l no-skip-hidden-recipients -d 'During decryption skip all anonymous recipients'
complete -c gpg -s a -d 'Create ASCII armored output'
complete -c gpg -s o -d 'Write output to file.   To write to stdout use - as the filename'
complete -c gpg -l export-filter -d 'These options define an import/export filter which are applied to the importe…'
complete -c gpg -l force-aead -d 'Force the use of AEAD encryption over MDC encryption'
complete -c gpg -l disable-mdc -d 'These options are obsolete and have no effect since GnuPG 2. 2. 8'
complete -c gpg -l no-include-key-block -d 'This option is used to embed the actual signing key into a data signature'
complete -c gpg -l include-certs -d 'to reply encrypted to the sender without using any online directories to look…'
complete -c gpg -l dry-run -d 'Don\'t make any changes (this is not completely implemented)'
complete -c gpg -l interactive -d 'Prompt before overwriting any files'
complete -c gpg -l logger-file -d 'Same as --logger-fd, except the logger data is written to file file'
complete -c gpg -l no-comments -d 'Use string as a comment string in cleartext signatures and ASCII armored mess…'
complete -c gpg -l no-emit-version -d 'Force inclusion of the version string in ASCII armored output'
complete -c gpg -s N -l set-notation -d 'Put the name value pair into the signature as notation data'
complete -c gpg -l cert-policy-url
complete -c gpg -l set-policy-url -d 'Use string as a Policy URL for signatures (rfc4880:5. 2. 3. 20)'
complete -c gpg -l no-for-your-eyes-only -d 'Set the `for your eyes only\' flag in the message'
complete -c gpg -l no-use-embedded-filename -d 'Try to create a file with a name as embedded in the data'
complete -c gpg -l no-throw-keyids -d 'Do not put the recipient key IDs into encrypted messages'
complete -c gpg -l no-escape-from-lines -d 'Because some mailers change lines starting with "From " to ">From " it is goo…'
complete -c gpg -l no-allow-non-selfsigned-uid -d 'Allow the import and use of keys with user IDs which are not self-signed'
complete -c gpg -l list-sigs -d 'Same as --list-keys, but the signatures are listed too'
complete -c gpg -l with-sig-list
complete -c gpg -l override-session-key-fd -d 'Don\'t use the public key but the session key string respective the session ke…'
complete -c gpg -l no-ask-sig-expire -d 'When making a data signature, prompt for an expiration time'
complete -c gpg -l no-ask-cert-expire -d 'When making a key signature, prompt for an expiration time'
complete -c gpg -l allow-multiple-messages
complete -c gpg -l no-textmode -d 'Treat input files as text and store them in the OpenPGP canonical text form w…'
complete -c gpg -l no-force-v3-sigs
complete -c gpg -l no-force-v4-certs -d 'These options are obsolete and have no effect since GnuPG 2. 1'
complete -c gpg -l no-show-photos -d 'Causes --list-keys, --list-signatures,'
complete -c gpg -l no-show-notation -d 'Show signature notations in the --list-signatures or --check-signatures listi…'
complete -c gpg -l no-show-policy-url -d 'Show policy URLs in the --list-signatures or --check-signatures listings as w…'
complete -c gpg -l aead-algo -d 'This option is deprecated and has no more effect since version 2. 3. 9'
complete -c gpg -l dump-cert -d '&D75F22C3F86E355877348498CDC92BD21010A480 By substring match'
complete -c gpg -o le -d 'The string value of the field must be less or equal than the value'
complete -c gpg -o lt -d 'The string value of the field must be less than the value'
complete -c gpg -o gt -d 'The string value of the field must be greater than the value'
complete -c gpg -o ge -d 'The string value of the field must be greater or equal than the value'
complete -c gpg -l ----------------------------- -d 'sec   dsa1024 2016-12-16 [SCA]       768E895903FC1C44045C8CB95EEBDB71E9E849D0…'

