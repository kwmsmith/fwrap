      subroutine char_array(charr)
        implicit none
        character(len=3), dimension(:,:), intent(inout) :: charr

        charr = "abc"

      end subroutine char_array

      subroutine char1_arr(charr)
        implicit none
        character, dimension(:,:), intent(inout) :: charr

        charr = "%"

      end subroutine char1_arr

      subroutine char_star(charr)
        implicit none
        character(*), dimension(:,:), intent(inout) :: charr

        charr = "123"
      end subroutine char_star
