function empty_func_c() bind(c, name='empty_func_c')
      use fwrap_ktp_mod
      implicit none
      interface
        function empty_func()
            implicit none
            integer :: empty_func
        end function empty_func
      end interface
      integer(fwrap_default_int) :: empty_func_c
      empty_func_c = empty_func()
end function fw_empty_func_c
