
! tests the number of dimensions with c_f_pointer since gfortran <=4.3.x
! has a buggy implementation.

subroutine D1(a)
    implicit none
    logical*4, intent(out), dimension(:) :: a

    a = .true.
    a(::2) = .false.

end subroutine D1

subroutine D2(a)
    implicit none
    logical*4, intent(out), dimension(:,:) :: a

    a = .true.
    a(::2, ::2) = .false.

end subroutine

subroutine D3(a)
    implicit none
    logical*4, intent(out), dimension(:,:,:) :: a

    a = .true.
    a(::2, :, :) = .false.

end subroutine
