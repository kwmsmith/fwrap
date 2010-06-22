
subroutine bar(a,b,c,d,e,f)
    implicit none
    integer*4, intent(inout) :: a
    real*4, intent(inout) :: b,c
    real*8, intent(inout) :: d
    integer*8, intent(inout) :: e
    double precision, intent(inout) :: f

    a = 1
    b = 2
    c = 2
    d = 3
    e = 4
    f = 5

end subroutine bar
