subroutine intents(inarg, inoutarg, outarg, nointent)
      implicit none
      integer, intent(in) :: inarg
      integer, intent(inout) :: inoutarg
      integer, intent(out) :: outarg
      integer :: nointent

      outarg = inarg + inoutarg
      inoutarg = inarg
      nointent = 3

end subroutine intents
