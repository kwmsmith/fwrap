
        subroutine assumed_shape_intents(a1, a2, a3, a4)
            implicit none
            real, dimension(:,:), intent(in) :: a1
            real, dimension(:,:), intent(inout) :: a2
            real, dimension(:,:), intent(out) :: a3
            real, dimension(:,:) :: a4

            a3 = a1 * 32
            a4 = a2 / 4.0

        end subroutine assumed_shape_intents
