[sample_logging]
format: ##logformat##
##if:mode=dev##
devmode: True
##endif##
##if:host!=localhost##
nolocalhost: True
##endif##
