

      subroutine char_args(ch, ch_in, ch_inout, ch_out)
        implicit none
        character*20 ch
        character(30), intent(in) :: ch_in
        character(len=10), intent(inout) :: ch_inout
        character(len=10), intent(out) :: ch_out

        ch = ch_in(1:19)
        ch_inout = ch_in(21:30)
        ch_out = ch_in(15:24)
      
      end subroutine char_args
