# openssl-ca.1ssl
# Autogenerated from man page /usr/share/man/man1/openssl-ca.1ssl.gz
complete -c 'openssl-ca.1ssl' -o help -d 'X Item "-help" Print out a usage message'
complete -c 'openssl-ca.1ssl' -o verbose -d 'X Item "-verbose" This prints extra details about the operations being perfor…'
complete -c 'openssl-ca.1ssl' -o quiet -d 'X Item "-quiet" This prints fewer details about the operations being performe…'
complete -c 'openssl-ca.1ssl' -o config -d 'X Item "-config filename" Specifies the configuration file to use'
complete -c 'openssl-ca.1ssl' -o name -o section -d 'X Item "-name section, -section section" Specifies the configuration file sec…'
complete -c 'openssl-ca.1ssl' -o in -d 'X Item "-in filename" An input filename containing a single certificate reque…'
complete -c 'openssl-ca.1ssl' -o inform -d 'X Item "-inform DER|PEM" The format to use when loading certificate request (…'
complete -c 'openssl-ca.1ssl' -o ss_cert -d 'X Item "-ss_cert filename" A single self-signed certificate to be signed by t…'
complete -c 'openssl-ca.1ssl' -o spkac -d 'X Item "-spkac filename" A file containing a single Netscape signed public ke…'
complete -c 'openssl-ca.1ssl' -o infiles -d 'X Item "-infiles" If present this should be the last option, all subsequent a…'
complete -c 'openssl-ca.1ssl' -o out -d 'X Item "-out filename" The output file to output certificates to'
complete -c 'openssl-ca.1ssl' -o outdir -d 'X Item "-outdir directory" The directory to output certificates to'
complete -c 'openssl-ca.1ssl' -o cert -d 'X Item "-cert filename" The CA certificate, which must match with -keyfile'
complete -c 'openssl-ca.1ssl' -o certform -d 'X Item "-certform DER|PEM|P12" The format of the data in certificate input fi…'
complete -c 'openssl-ca.1ssl' -o keyfile -d 'X Item "-keyfile filename|uri" The CA private key to sign certificate request…'
complete -c 'openssl-ca.1ssl' -o keyform -d 'X Item "-keyform DER|PEM|P12|ENGINE" The format of the private key input file…'
complete -c 'openssl-ca.1ssl' -o sigopt -d 'X Item "-sigopt nm:v" Pass options to the signature algorithm during sign ope…'
complete -c 'openssl-ca.1ssl' -o vfyopt -d 'X Item "-vfyopt nm:v" Pass options to the signature algorithm during verify o…'
complete -c 'openssl-ca.1ssl' -o key -d 'X Item "-key password" The password used to encrypt the private key'
complete -c 'openssl-ca.1ssl' -o passin -d 'X Item "-passin arg" The key password source for key files and certificate PK…'
complete -c 'openssl-ca.1ssl' -o selfsign -d 'X Item "-selfsign" Indicates the issued certificates are to be signed with th…'
complete -c 'openssl-ca.1ssl' -o notext -d 'X Item "-notext" Don\'t output the text form of a certificate to the output fi…'
complete -c 'openssl-ca.1ssl' -o dateopt -d 'X Item "-dateopt" Specify the date output format'
complete -c 'openssl-ca.1ssl' -o startdate -o not_before -d 'X Item "-startdate date, -not_before date" This allows the start date to be e…'
complete -c 'openssl-ca.1ssl' -o enddate -o not_after -d 'X Item "-enddate date, -not_after date" This allows the expiry date to be exp…'
complete -c 'openssl-ca.1ssl' -o days -d 'X Item "-days arg" The number of days from today to certify the certificate f…'
complete -c 'openssl-ca.1ssl' -o md -d 'X Item "-md alg" The message digest to use'
complete -c 'openssl-ca.1ssl' -o policy -d 'X Item "-policy arg" This option defines the CA "policy" to use'
complete -c 'openssl-ca.1ssl' -o msie_hack -d 'X Item "-msie_hack" This is a deprecated option to make this command work wit…'
complete -c 'openssl-ca.1ssl' -o preserveDN -d 'X Item "-preserveDN" Normally the DN order of a certificate is the same as th…'
complete -c 'openssl-ca.1ssl' -o noemailDN -d 'X Item "-noemailDN" The DN of a certificate can contain the EMAIL field if pr…'
complete -c 'openssl-ca.1ssl' -o batch -d 'X Item "-batch" This sets the batch mode'
complete -c 'openssl-ca.1ssl' -o extensions -d 'X Item "-extensions section" The section of the configuration file containing…'
complete -c 'openssl-ca.1ssl' -o extfile -d 'X Item "-extfile file" An additional configuration file to read certificate e…'
complete -c 'openssl-ca.1ssl' -o subj -d 'X Item "-subj arg" Supersedes subject name given in the request'
complete -c 'openssl-ca.1ssl' -o utf8 -d 'X Item "-utf8" This option causes field values to be interpreted as UTF8 stri…'
complete -c 'openssl-ca.1ssl' -o create_serial -d 'X Item "-create_serial" If reading serial from the text file as specified in …'
complete -c 'openssl-ca.1ssl' -o rand_serial -d 'X Item "-rand_serial" Generate a large random number to use as the serial num…'
complete -c 'openssl-ca.1ssl' -o multivalue-rdn -d 'X Item "-multivalue-rdn" This option has been deprecated and has no effect'
complete -c 'openssl-ca.1ssl' -o rand -o writerand -d 'X Item "-rand files, -writerand file" See "Random State Options" in openssl\\|…'
complete -c 'openssl-ca.1ssl' -o engine -d 'X Item "-engine id" See "Engine Options" in openssl\\|(1)'
complete -c 'openssl-ca.1ssl' -o provider -d 'X Item "-provider name"'
complete -c 'openssl-ca.1ssl' -o provider-path -d 'X Item "-provider-path path"'
complete -c 'openssl-ca.1ssl' -o propquery -d 'See "Provider Options" in openssl(1), provider(7), and property(7)'
complete -c 'openssl-ca.1ssl' -o gencrl
complete -c 'openssl-ca.1ssl' -o crl_lastupdate
complete -c 'openssl-ca.1ssl' -o crl_nextupdate
complete -c 'openssl-ca.1ssl' -o crldays
complete -c 'openssl-ca.1ssl' -o crlhours
complete -c 'openssl-ca.1ssl' -o crlsec
complete -c 'openssl-ca.1ssl' -o revoke
complete -c 'openssl-ca.1ssl' -o valid
complete -c 'openssl-ca.1ssl' -o status
complete -c 'openssl-ca.1ssl' -o updatedb
complete -c 'openssl-ca.1ssl' -o crl_reason
complete -c 'openssl-ca.1ssl' -o crl_hold
complete -c 'openssl-ca.1ssl' -o crl_compromise
complete -c 'openssl-ca.1ssl' -o crl_CA_compromise
complete -c 'openssl-ca.1ssl' -o crlexts

