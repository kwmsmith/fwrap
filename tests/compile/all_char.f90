

      subroutine char_arg(ch, ch_in)
        implicit none
        character(len=20) :: ch
        character(*) :: ch_in

        ch = ch_in

      end subroutine char_arg

      subroutine char_star(ch, ch_in, ch_out, ch_inout)
        implicit none
        character(*) ch
        character(len=*), intent(in) :: ch_in
        character(*), intent(out) :: ch_out
        character(*), intent(inout) :: ch_inout

        ch = ch_in

        ch_out = ch_inout

      end subroutine char_star

      subroutine char_len_x(ch, ch_in, ch_out, ch_inout)
        implicit none
        character*20 :: ch
        character*10, intent(in) :: ch_in
        character(len=5), intent(out) :: ch_out
        character(len=1), intent(inout) :: ch_inout

        ch_inout = ch(2:2)
        ch_out = ch_in(1:5)
        ch = ch_in // ch_out // ch_out

      end subroutine char_len_x
