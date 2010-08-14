module used
implicit none

integer, parameter :: dflt_int = kind(0)

end module used

subroutine s1(a)
use used
implicit none
integer(kind=dflt_int), intent(inout) :: a
      a = 10
end subroutine s1
