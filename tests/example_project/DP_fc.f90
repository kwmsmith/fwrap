function fw_empty_func() bind(c, name='empty_func')
      use fwrap_ktp_mod
      implicit none
      interface
        function empty_func()
            implicit none
            integer :: empty_func
        end function empty_func
      end interface
      integer(fwrap_default_int) :: fw_empty_func
      fw_empty_func = empty_func()
end function fw_empty_func
