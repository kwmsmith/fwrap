

      function ret_arr(a, b)
        implicit none
        integer, intent(in) :: a, b
        integer, dimension(a, b) :: ret_arr

        ret_arr = 100
        ret_arr(1,:) = 0

      end function ret_arr
