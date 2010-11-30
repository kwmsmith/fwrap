! A lot of explicit array features are tested in all_X_arrays
! testcases. This testcase is concerned with passing in a lower
! shape on the first dimension to truncate an array.

      function explicit_shape_sum_1d(n, arr) result(res)
        implicit none
        integer, intent(in) :: n
        integer, dimension(n), intent(in) :: arr
        integer :: i
        integer :: res
        res = 0
        do i = 1, n
           res = res + arr(i)
        enddo
      end function

      function explicit_shape_sum_2d(n1, n2, arr) result(res)
        implicit none
        integer, intent(in) :: n1, n2
        integer, dimension(n1, n2), intent(in) :: arr
        integer :: i, j
        integer :: res
        res = 0
        do j = 1, n2
           do i = 1, n1
              res = res + arr(i, j)
           enddo
        enddo
      end function
