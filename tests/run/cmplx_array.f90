      subroutine complex_array(c)
        implicit none
        complex(kind=8), dimension(:,:), intent(inout) :: c

        c = cmplx(1, 2)

      end subroutine complex_array
