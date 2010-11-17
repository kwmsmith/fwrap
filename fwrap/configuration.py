def add_configure_options(add_option):
    # Add configuration options. add_option is a callback,
    # and might either be add_option from optparse or
    # add_argument from argparse.

    # This is just a place-holder until merged with f77 branch.
    add_option('--dummy', action='store_true',
               help='dummy development configuration option')
    

