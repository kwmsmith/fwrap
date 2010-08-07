subroutine simple_subr(iarg, rarg, larg, carg, charg)
    implicit none
    integer, intent(inout) :: iarg
    real, intent(inout) :: rarg
    logical, intent(inout) :: larg
    complex, intent(inout) :: carg
    character(len=1), intent(inout) :: charg

    iarg = 1
    rarg = 2.0E0
    larg = .true.
    carg = (3.0E0, 4.0E0)
    charg = "E"

end subroutine simple_subr
