
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

      subroutine char1(ch)
        implicit none
        character*20 :: ch
        ch = "aoeuidhtns"
      end subroutine char1

      subroutine char2(ch)
        implicit none
        character*10, intent(in) :: ch
        character*10 :: dummy
        dummy = ch
      end subroutine char2

      subroutine char3(ch)
        implicit none
        character(len=5), intent(out) :: ch
        ch = "',.py"
      end subroutine char3

      subroutine char4(ch)
        implicit none
        character(len=1), intent(inout) :: ch
        character(*), parameter :: cp = "a^eu"
        ch = cp(2:2)
      end subroutine char4

      subroutine char_len_x(ch, ch_in, ch_out, ch_inout)
        implicit none
        character*20 :: ch
        character*10, intent(in) :: ch_in
        character(len=5), intent(out) :: ch_out
        character(len=1), intent(inout) :: ch_inout

        ch_out = ch_inout // ch_in(1:4)
        ch = ch_in // ch_out // ch_out
        ch_inout = 'a'

      end subroutine char_len_x

      subroutine len_1_args(a, b, c)
        implicit none
        character :: a
        character, intent(inout) :: b
        character, intent(out) :: c

        a = b
        c = b
      end subroutine len_1_args
