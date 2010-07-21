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
