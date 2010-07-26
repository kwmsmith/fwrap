      subroutine const_expr(a)
        implicit none
        integer, dimension(10:20), intent(inout) :: a
        integer i

        do i = 10, 20
            a(i) = i
        enddo

      end subroutine const_expr

      subroutine arg_expr(a, n1, n2)
        implicit none
        integer, intent(in) :: n1, n2
        integer, dimension(n1-n1+3:n1+n2*2) :: a

        a = 12

      end subroutine arg_expr

      subroutine param_expr(a)
        implicit none
        integer, parameter :: d1=1
        integer, parameter :: d2=d1+2+int(3.0)
        integer, parameter :: d3=d1+d2
        integer, dimension(d1:d2+d3, d2:d3+1, -d3:0) :: a

        integer i,j,k

        do k = lbound(a, 3), ubound(a, 3)
            do j = lbound(a, 2), ubound(a, 2)
                do i = lbound(a, 1), ubound(a, 1)
                    a(i,j,k) = k + j + i
                enddo
            enddo
        enddo

      end subroutine param_expr
