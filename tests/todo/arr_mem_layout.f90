

      subroutine mem_layout(arg)
        implicit none
        integer, dimension(:,:), intent(inout) :: arg

        integer i,j

        ! iterate through the array 2nd dimension first, in 'C' order
        do i = 1, size(arg, 1)
            do j = 1, size(arg, 2)
                print *, arg(i,j)
            enddo
        enddo

      end subroutine mem_layout
