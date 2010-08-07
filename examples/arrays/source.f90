subroutine array_args(iarg, rarg, carg, larg, charg)
      implicit none
      integer, dimension(:), intent(inout) :: iarg
      real, dimension(:), intent(inout) :: rarg
      complex, dimension(:), intent(inout) :: carg
      logical, dimension(:), intent(inout) :: larg
      character(len=10), dimension(:), intent(inout) :: charg

      iarg = 1
      rarg = 2.0E0
      carg = (3.0E0, 4.0E0)
      larg = .true.
      charg = "0123456789"

end subroutine array_args
