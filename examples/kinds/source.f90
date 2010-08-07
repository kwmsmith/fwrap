subroutine non_default(iarg, rarg, carg, larg)
    implicit none
    integer*8 :: iarg
    real(kind=8) :: rarg
    complex(kind=8) :: carg
    logical*8 :: larg

    iarg = 3
    rarg = 4.0_8
    carg = (10.0_8, 11.0_8)
    larg = logical(.true., kind=kind(larg))

end subroutine non_default
